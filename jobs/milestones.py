from __future__ import annotations

# jobs/milestones.py
#
# Private DMs at 1, 3 and 10 hours of unmuted voice time.
# The 3-hour DM also asks the testimonial questions (once per member).
#
# Hours count from MILESTONE_START_KV (set per server on first run), so old
# voice data (which included muted time and downtime gaps) never counts.
# Checked when a voice session ends, so the DM arrives after the member
# leaves voice, never while they are talking.

import logging
import time

import discord

from db.repo import Repo

log = logging.getLogger("jobs.milestones")

MILESTONE_START_KV = "milestones_count_from"
TESTIMONIAL_SENT_PREFIX = "testimonial_dm_sent:"   # shared with commands/testimonials.py
ADMIN_LOG_CHANNEL_ID = 1490322440788644011          # collected-testimonials

MILESTONE_HOURS = (1, 3, 10)
TESTIMONIAL_AT_HOURS = 3


def _achievement_id(hours: int) -> str:
    return f"milestone_{hours}h"


EN_MESSAGES = {
    1: (
        "You've now spent 1 hour speaking in voice. "
        "That's a full hour of English out loud. Good work."
    ),
    3: "3 hours of speaking in voice. That's real practice, and you did it.",
    10: (
        "10 hours of speaking in voice. "
        "Think back to your first time in a channel. Look how far you've come."
    ),
}

NL_MESSAGES = {
    1: (
        "Je hebt nu 1 uur in voice gesproken. "
        "Een heel uur Nederlands hardop. Goed bezig."
    ),
    3: "3 uur spreken in voice. Dat is echt oefenen, en jij hebt het gedaan.",
    10: (
        "10 uur spreken in voice. "
        "Denk terug aan je eerste keer in een kanaal. Kijk hoe ver je nu bent."
    ),
}

EN_TESTIMONIAL = (
    "Can I ask you three quick questions?\n\n"
    "1. What was your worst moment speaking English before you joined? "
    "One real moment, with details.\n"
    "2. What can you do now that you couldn't do then?\n"
    "3. Where are you from and what do you do?\n\n"
    "A voice message is perfect. You decide if it stays private."
)

NL_TESTIMONIAL = (
    "Mag ik je drie korte vragen stellen?\n\n"
    "1. Wat was je slechtste moment met Nederlands spreken voordat je lid werd? "
    "Eén echt moment, met details.\n"
    "2. Wat kun je nu dat je toen nog niet kon?\n"
    "3. Waar kom je vandaan en wat doe je?\n\n"
    "Een spraakbericht is perfect. Jij bepaalt of het privé blijft."
)


def build_milestone_text(hours: int, *, is_nl: bool, ask_testimonial: bool) -> str:
    text = (NL_MESSAGES if is_nl else EN_MESSAGES)[hours]
    if ask_testimonial:
        text += "\n\n" + (NL_TESTIMONIAL if is_nl else EN_TESTIMONIAL)
    return text


class Milestones:
    def __init__(self, *, bot: discord.Client, repo: Repo, dutch_guild_id: int | None) -> None:
        self.bot = bot
        self.repo = repo
        self.dutch_guild_id = dutch_guild_id

    async def ensure_start(self, guild_id: int) -> int:
        """First run per server sets the count-from time. Returns it."""
        raw = await self.repo.kv_get(guild_id, MILESTONE_START_KV)
        if raw:
            return int(raw)
        now = int(time.time())
        await self.repo.kv_set(guild_id, MILESTONE_START_KV, str(now))
        log.info("Milestones: counting from %s guild=%s", now, guild_id)
        return now

    async def check(self, guild_id: int, user_id: int) -> None:
        try:
            await self._check(guild_id, user_id)
        except Exception:
            log.exception("Milestones: check failed guild=%s user=%s", guild_id, user_id)

    async def _check(self, guild_id: int, user_id: int) -> None:
        start = await self.ensure_start(guild_id)
        seconds = await self.repo.user_voice_seconds_since(guild_id, user_id, start)

        reached = [h for h in MILESTONE_HOURS if seconds >= h * 3600]
        if not reached:
            return

        # Mark every reached milestone. Only DM the highest new one,
        # so a long session never sends two messages at once.
        now = int(time.time())
        new = [h for h in reached if await self.repo.achievement_award_once(guild_id, user_id, _achievement_id(h), now)]
        if not new:
            return
        hours = max(new)

        is_nl = self.dutch_guild_id is not None and guild_id == self.dutch_guild_id
        testimonial_key = f"{TESTIMONIAL_SENT_PREFIX}{user_id}"
        ask_testimonial = (
            hours >= TESTIMONIAL_AT_HOURS
            and not await self.repo.kv_get(guild_id, testimonial_key)
        )

        member = await self._resolve_member(guild_id, user_id)
        if member is None:
            return

        try:
            await member.send(build_milestone_text(hours, is_nl=is_nl, ask_testimonial=ask_testimonial))
        except discord.Forbidden:
            log.info("Milestones: DM blocked user=%s hours=%s", user_id, hours)
            return
        except Exception:
            log.exception("Milestones: DM failed user=%s hours=%s", user_id, hours)
            return

        log.info("Milestones: DM sent user=%s guild=%s hours=%s testimonial=%s", user_id, guild_id, hours, ask_testimonial)

        if ask_testimonial:
            await self.repo.kv_set(guild_id, testimonial_key, str(now))
            await self._log_testimonial_ask(member, is_nl)

    async def _resolve_member(self, guild_id: int, user_id: int) -> discord.Member | None:
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return None
        member = guild.get_member(user_id)
        if member is not None:
            return member
        try:
            return await guild.fetch_member(user_id)
        except Exception:
            return None

    async def _log_testimonial_ask(self, member: discord.Member, is_nl: bool) -> None:
        try:
            ch = self.bot.get_channel(ADMIN_LOG_CHANNEL_ID) or await self.bot.fetch_channel(ADMIN_LOG_CHANNEL_ID)
            if isinstance(ch, discord.TextChannel):
                lang = "NL" if is_nl else "EN"
                await ch.send(
                    f"📨 DM sent to **{member.display_name}** (`{member.id}`) [{lang}], "
                    f"🎙️ {TESTIMONIAL_AT_HOURS}h voice milestone"
                )
        except Exception:
            log.exception("Milestones: failed to log testimonial ask user=%s", member.id)
