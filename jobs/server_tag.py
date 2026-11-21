from __future__ import annotations

# jobs/server_tag.py
#
# Server Tag adoption (EN server only). Members can wear our "CAFE" tag next to
# their name in every server; clicking it opens our server profile.
#
# - Detects who wears it: on member/user updates, plus a daily pass over the
#   member cache (no API calls, so no rate limits).
# - Thanks a member once, ever, the first time they wear it.
# - Gives other code a short "wear our tag" line for DMs to members with 1h+
#   of speaking time (see jobs/milestones.py and voice/community_tracker.py).
#   It never DMs anyone only to ask.

import asyncio
import datetime as dt
import logging
import time
from typing import Any
from zoneinfo import ZoneInfo

import discord
from discord.ext import tasks

log = logging.getLogger("jobs.server_tag")

TZ = ZoneInfo("Europe/Amsterdam")
DAILY_CHECK_TIME = dt.time(4, 13, tzinfo=TZ)
ASK_EVERY_SECONDS = 28 * 86400     # weekly recap line: at most once every 4 weeks
MIN_SPEAKING_SECONDS = 3600        # never ask members under 1 hour
THANKS_GAP_SECONDS = 1.5           # spacing between thank-you DMs in the daily pass

TAG_ASK_LINE = (
    "Want to show you're part of the café? Wear our CAFE tag: open your profile, "
    "choose Server Tag, then Online English Café."
)
THANKS_DM = "Thanks for wearing the CAFE tag! It helps other learners find us."

SUPPORTED = hasattr(discord.Member, "primary_guild") or hasattr(discord.User, "primary_guild")


def wears_tag(user: discord.abc.User, guild_id: int) -> bool:
    pg = getattr(user, "primary_guild", None)
    if pg is None:
        return False
    return getattr(pg, "id", None) == guild_id and bool(getattr(pg, "identity_enabled", False))


class ServerTag:
    def __init__(self, *, bot: discord.Client, repo: Any, guild_id: int) -> None:
        self.bot = bot
        self.repo = repo
        self.guild_id = guild_id
        self.enabled = SUPPORTED
        if not self.enabled:
            log.warning("ServerTag: this discord.py has no primary_guild; Server Tag feature is off")
            return
        self._daily.start()

    # -------------------------
    # Detection
    # -------------------------
    async def check_member(self, member: discord.abc.User, *, thank: bool = True) -> bool:
        """Record the member's current tag state. Returns True if they wear it."""
        if not self.enabled or getattr(member, "bot", False):
            return False
        wearing = wears_tag(member, self.guild_id)
        now = int(time.time())
        first_time = await self.repo.tag_record(self.guild_id, member.id, wearing, now)
        if first_time:
            log.info("ServerTag: first time wearing user=%s", member.id)
        if wearing and thank and await self.repo.tag_mark_thanked(self.guild_id, member.id, now):
            try:
                await member.send(THANKS_DM)
                log.info("ServerTag: thanked user=%s", member.id)
            except Exception as e:
                log.debug("ServerTag: thank-you DM failed user=%s (%s)", member.id, e)
            return True
        return wearing

    async def on_user_changed(self, before: discord.abc.User, after: discord.abc.User) -> None:
        if not self.enabled:
            return
        if wears_tag(before, self.guild_id) == wears_tag(after, self.guild_id):
            return
        guild = self.bot.get_guild(self.guild_id)
        if guild is None or guild.get_member(after.id) is None:
            return  # only members of the EN server
        try:
            await self.check_member(after)
        except Exception:
            log.exception("ServerTag: update check failed user=%s", after.id)

    @tasks.loop(time=DAILY_CHECK_TIME)
    async def _daily(self) -> None:
        await self.run_daily()

    @_daily.before_loop
    async def _before(self) -> None:
        await self.bot.wait_until_ready()

    async def run_daily(self) -> int:
        guild = self.bot.get_guild(self.guild_id)
        if guild is None:
            return 0
        wearing = 0
        for member in list(guild.members):
            if member.bot:
                continue
            try:
                was_thanked_before = (await self.repo.tag_get(self.guild_id, member.id) or {}).get("thanked_at")
                if await self.check_member(member):
                    wearing += 1
                    if not was_thanked_before:
                        await asyncio.sleep(THANKS_GAP_SECONDS)
            except Exception:
                log.exception("ServerTag: daily check failed user=%s", member.id)
        log.info("ServerTag: daily check done wearing=%s", wearing)
        return wearing

    # -------------------------
    # Asking (a line inside DMs the member gets anyway)
    # -------------------------
    async def ask_line_for_milestone(self, member: discord.Member) -> str | None:
        """For the 3h milestone DM: only non-wearers (3h means 1h+ already)."""
        if not self.enabled or member.guild.id != self.guild_id:
            return None
        if await self.check_member(member, thank=False):
            return None
        await self.repo.tag_mark_asked(self.guild_id, member.id, int(time.time()))
        return TAG_ASK_LINE

    async def ask_line_for_recap(self, member: discord.Member, speaking_seconds: int) -> str | None:
        """For the weekly recap DM: 1h+ speakers who don't wear it, at most once every 4 weeks."""
        if not self.enabled or member.guild.id != self.guild_id:
            return None
        if speaking_seconds < MIN_SPEAKING_SECONDS:
            return None
        if await self.check_member(member, thank=False):
            return None
        state = await self.repo.tag_get(self.guild_id, member.id) or {}
        now = int(time.time())
        if state.get("last_asked_at") and now - int(state["last_asked_at"]) < ASK_EVERY_SECONDS:
            return None
        await self.repo.tag_mark_asked(self.guild_id, member.id, now)
        return TAG_ASK_LINE
