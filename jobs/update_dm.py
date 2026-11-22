from __future__ import annotations

# jobs/update_dm.py
#
# One-off "what's new" DM to recent speakers (EN server only).
# Recipients: members still in the server with voice time in the last 60 days,
# not bots, not joined in the last 7 days, not opted out of update DMs, and
# not already sent this campaign. Sent slowly in the background.

import asyncio
import logging
import random
import time
from typing import Any, Awaitable, Callable

import discord

log = logging.getLogger("jobs.update_dm")

CAMPAIGN = "update_2026_11"
LOOKBACK_DAYS = 60
NEW_MEMBER_DAYS = 7
GAP_SECONDS = (3.0, 5.0)
MAX_RATE_LIMITS_IN_A_ROW = 3

UPDATE_TEXT = """\
Hi {name}! We made some changes to the café:
- Café Hour: every day at 19:00 Amsterdam time in Open Conversation. Other learners will be there.
- /profile: see your speaking time, the people you talked with and your achievements.
- Speaking roles: you get a new role at 1, 3, 10, 20, 50 and 100 hours.
- The CAFE tag: show you're part of the café next to your name.
See you in voice!\
"""


class UpdateOptOutView(discord.ui.View):
    """Persistent button under update DMs. The member is interaction.user."""

    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(label="Don't send me update messages", style=discord.ButtonStyle.secondary, custom_id="update_dm:optout:v1")
    async def optout(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        bot = interaction.client
        await bot.repo.dm_optout_set(bot.guild_id, interaction.user.id, "updates", int(time.time()))
        log.info("UpdateDM: opt-out user=%s", interaction.user.id)
        button.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send("Done. You won't get update messages from the café anymore.")


class UpdateDM:
    def __init__(self, *, bot: discord.Client, repo: Any, guild_id: int) -> None:
        self.bot = bot
        self.repo = repo
        self.guild_id = guild_id
        self._task: asyncio.Task | None = None

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def recipients(self) -> list[discord.Member]:
        guild = self.bot.get_guild(self.guild_id)
        if guild is None:
            return []
        now = time.time()
        since = int(now - LOOKBACK_DAYS * 86400)
        ids = await self.repo.broadcast_recipients(self.guild_id, CAMPAIGN, since)
        result = []
        for uid in ids:
            member = guild.get_member(uid)
            if member is None or member.bot:
                continue
            if member.joined_at and now - member.joined_at.timestamp() < NEW_MEMBER_DAYS * 86400:
                continue  # they just got the welcome DM
            result.append(member)
        return result

    def text_for(self, member: discord.abc.User) -> str:
        return UPDATE_TEXT.format(name=member.display_name)

    def start(self, members: list[discord.Member], report: Callable[[str], Awaitable[None]]) -> bool:
        if self.running:
            return False
        self._task = asyncio.create_task(self._send_all(members, report))
        return True

    async def _send_all(self, members: list[discord.Member], report: Callable[[str], Awaitable[None]]) -> None:
        sent = closed = skipped = 0
        rate_limited_in_a_row = 0
        stopped = False
        for member in members:
            # Re-check right before sending: opt-outs and earlier sends win.
            if member.id not in {m.id for m in await self.recipients()}:
                skipped += 1
                continue
            try:
                await member.send(self.text_for(member), view=UpdateOptOutView())
                await self.repo.broadcast_mark(self.guild_id, member.id, CAMPAIGN, "sent", int(time.time()))
                sent += 1
                rate_limited_in_a_row = 0
            except discord.Forbidden:
                await self.repo.broadcast_mark(self.guild_id, member.id, CAMPAIGN, "closed", int(time.time()))
                closed += 1
                log.debug("UpdateDM: DMs closed user=%s", member.id)
            except discord.HTTPException as e:
                if e.status == 429:
                    rate_limited_in_a_row += 1
                    log.warning("UpdateDM: rate limited (%s in a row)", rate_limited_in_a_row)
                    if rate_limited_in_a_row > MAX_RATE_LIMITS_IN_A_ROW:
                        log.warning("UpdateDM: stopping after %s rate limits in a row", rate_limited_in_a_row)
                        stopped = True
                        break
                    await asyncio.sleep(30)
                else:
                    log.warning("UpdateDM: send failed user=%s (%s)", member.id, e)
            await asyncio.sleep(random.uniform(*GAP_SECONDS))

        optouts = await self.repo.dm_optout_count(self.guild_id, "updates")
        summary = (
            f"Update DM ({CAMPAIGN}){' **stopped early** (rate limits)' if stopped else ''}: "
            f"sent **{sent}**, closed DMs **{closed}**, skipped **{skipped}**, "
            f"opted out (all time) **{optouts}**, total in this run **{len(members)}**."
        )
        log.info(summary)
        try:
            await report(summary)
        except Exception:
            log.exception("UpdateDM: could not post the summary")
