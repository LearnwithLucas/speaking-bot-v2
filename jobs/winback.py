from __future__ import annotations

# jobs/winback.py
#
# One DM after 14 days without voice time. Once per absence: the member only
# becomes eligible again after they come back to voice and then stop again.
#
# Runs once a day. Only members whose last voice time was 14 to 21 days ago
# are DM'd, so people who left long ago never get a sudden message.

import asyncio
import datetime as dt
import logging
import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord
from discord.ext import tasks

from db.repo import Repo
from jobs.welcome import WelcomeTableView

log = logging.getLogger("jobs.winback")

MIN_DAYS = 14
MAX_DAYS = 21
RUN_HOUR = 17          # Europe/Amsterdam
RUN_MINUTE = 7
DM_GAP_SECONDS = 1.5   # stay well under Discord rate limits
KV_LAST_RUN = "winback_last_run_date"

EN_WINBACK_DM = """\
Hey, it's been a little while since you were in voice. \
No need to explain anything.

Want to start small again? Book a Table for 2: \
one short chat with one other member.\
"""

NL_WINBACK_DM = """\
Hey, je bent al even niet in voice geweest. \
Je hoeft niets uit te leggen.

Wil je weer klein beginnen? Plan een Tafel voor 2: \
één kort gesprek met één ander lid.\
"""


def _amsterdam_now() -> dt.datetime:
    try:
        return dt.datetime.now(tz=ZoneInfo("Europe/Amsterdam"))
    except ZoneInfoNotFoundError:
        return dt.datetime.now()


class WinbackJob:
    def __init__(self, *, bot: discord.Client, repo: Repo, guild_id: int, dutch_guild_id: int | None) -> None:
        self.bot = bot
        self.repo = repo
        self.guild_id = guild_id
        self.dutch_guild_id = dutch_guild_id
        self._tick.start()

    @tasks.loop(minutes=1)
    async def _tick(self) -> None:
        now = _amsterdam_now()
        if (now.hour, now.minute) != (RUN_HOUR, RUN_MINUTE):
            return
        today = now.date().isoformat()
        if await self.repo.kv_get(self.guild_id, KV_LAST_RUN) == today:
            return
        await self.repo.kv_set(self.guild_id, KV_LAST_RUN, today)
        await self.run_once()

    @_tick.before_loop
    async def _before(self) -> None:
        await self.bot.wait_until_ready()

    async def run_once(self) -> int:
        sent = 0
        for guild_id, is_nl in ((self.guild_id, False), (self.dutch_guild_id, True)):
            if not guild_id:
                continue
            try:
                sent += await self._run_guild(guild_id, is_nl)
            except Exception:
                log.exception("Winback: run failed guild=%s", guild_id)
        return sent

    async def _run_guild(self, guild_id: int, is_nl: bool) -> int:
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            log.warning("Winback: guild %s not found", guild_id)
            return 0

        now = int(time.time())
        candidates = await self.repo.winback_candidates(guild_id, now, MIN_DAYS, MAX_DAYS)
        sent = 0
        for user_id, _last_at in candidates:
            member = guild.get_member(user_id)
            if member is None or member.bot:
                continue  # left the server

            # Mark first, so a crash mid-run never sends the same DM twice.
            await self.repo.user_state_mark_inactivity_nudge(guild_id, user_id, now)
            try:
                await member.send(
                    NL_WINBACK_DM if is_nl else EN_WINBACK_DM,
                    view=WelcomeTableView(is_nl=is_nl),
                )
                sent += 1
                log.info("Winback: DM sent user=%s guild=%s", user_id, guild_id)
            except discord.Forbidden:
                log.info("Winback: DM blocked user=%s", user_id)
            except Exception:
                log.exception("Winback: DM failed user=%s", user_id)
            await asyncio.sleep(DM_GAP_SECONDS)

        log.info("Winback: guild=%s candidates=%s sent=%s", guild_id, len(candidates), sent)
        return sent
