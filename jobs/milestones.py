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
from typing import Any

import discord

import asyncio

from config import MILESTONE_ANNOUNCE_CHANNEL_ID, MILESTONE_ROLES
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


PROFILE_LINE_EN = "See your full profile: /profile"
PROFILE_LINE_NL = "Bekijk je hele profiel: /profile"


def build_milestone_text(hours: int, *, is_nl: bool, ask_testimonial: bool) -> str:
    text = (NL_MESSAGES if is_nl else EN_MESSAGES)[hours]
    if ask_testimonial:
        text += "\n\n" + (NL_TESTIMONIAL if is_nl else EN_TESTIMONIAL)
    return text + "\n\n" + (PROFILE_LINE_NL if is_nl else PROFILE_LINE_EN)


# Public shout-outs (EN only). First Words (15 min) gets none.
SHOUTOUT_HOURS = (1, 3, 10, 20, 50, 100)
SHOUTOUTS_SEEDED_KV = "milestone_shoutouts_seeded_v1"


def shoutout_text(mention: str, hours: int) -> str:
    amount = "1 hour" if hours == 1 else f"{hours} hours"
    return f"{mention} just reached {amount} of speaking practice in the café. Say congrats!"


def highest_shoutout(seconds: int) -> int | None:
    reached = [h for h in SHOUTOUT_HOURS if seconds >= h * 3600]
    return max(reached) if reached else None


class ShoutoutOptView(discord.ui.View):
    """Persistent buttons under milestone DMs (EN). The member is interaction.user."""

    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(label="Don't post my milestones publicly", style=discord.ButtonStyle.secondary, custom_id="milestone_shoutout:off:v1")
    async def off(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await _set_shoutouts(interaction, False)

    @discord.ui.button(label="Post my milestones again", style=discord.ButtonStyle.secondary, custom_id="milestone_shoutout:on:v1")
    async def on(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await _set_shoutouts(interaction, True)


async def _set_shoutouts(interaction: discord.Interaction, enabled: bool) -> None:
    bot = interaction.client
    guild_id = getattr(bot, "guild_id", None)
    repo = getattr(bot, "repo", None)
    if not guild_id or repo is None:
        await interaction.response.send_message("That didn't work right now. Try again in a moment.")
        return
    await repo.milestone_shoutouts_set(guild_id, interaction.user.id, enabled, int(time.time()))
    log.info("Milestones: shout-outs %s user=%s", "on" if enabled else "off", interaction.user.id)
    await interaction.response.send_message(
        "Done. Your milestones will be posted in the café again."
        if enabled
        else "Done. Your milestones won't be posted publicly. You still get your role and this DM."
    )


def _role_rank(role_id: int) -> int:
    for index, (_t, _n, rid) in enumerate(MILESTONE_ROLES):
        if rid == role_id:
            return index
    return -1


def target_role_id(seconds: int) -> int | None:
    """Role ID of the highest milestone reached that has a role configured."""
    target = None
    for threshold, _name, role_id in MILESTONE_ROLES:
        if role_id and seconds >= threshold:
            target = role_id
    return target


class Milestones:
    def __init__(
        self,
        *,
        bot: discord.Client,
        repo: Repo,
        dutch_guild_id: int | None,
        role_guild_id: int | None = None,
        hosts: Any = None,
    ) -> None:
        self.bot = bot
        self.repo = repo
        self.dutch_guild_id = dutch_guild_id
        # Milestone roles and host invites run on this server only (EN for now).
        self.role_guild_id = role_guild_id
        self.hosts = hosts
        self._locks: dict[tuple[int, int], asyncio.Lock] = {}
        self._announce_warned = False
        missing = [name for _t, name, rid in MILESTONE_ROLES if not rid]
        if missing:
            log.warning("Milestones: no role ID set for %s; those roles are skipped", ", ".join(missing))

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
        # One check per member at a time: two quick voice changes must not
        # race and leave two milestone roles behind.
        lock = self._locks.setdefault((guild_id, user_id), asyncio.Lock())
        async with lock:
            try:
                await self._check(guild_id, user_id)
            except Exception:
                log.exception("Milestones: check failed guild=%s user=%s", guild_id, user_id)

    async def _check(self, guild_id: int, user_id: int) -> None:
        start = await self.ensure_start(guild_id)
        seconds = await self.repo.user_voice_seconds_since(guild_id, user_id, start)
        is_role_guild = guild_id == self.role_guild_id
        member = await self._resolve_member(guild_id, user_id)

        # 1. Role: highest reached, every other milestone role removed.
        if is_role_guild and member is not None:
            await self.sync_role(member, seconds)

        # 2. Private DM (1h, 3h, 10h).
        if member is not None:
            await self._maybe_send_dm(member, guild_id, seconds, with_opt_buttons=is_role_guild)

        # 3. Public shout-out for the highest tier, once ever.
        if is_role_guild and member is not None:
            await self._maybe_shoutout(member, seconds)

        # 4. Conversation Host invite at 20h.
        if is_role_guild and member is not None and self.hosts is not None:
            await self.hosts.maybe_invite(member, seconds)

    async def _maybe_send_dm(self, member: discord.Member, guild_id: int, seconds: int, *, with_opt_buttons: bool) -> None:
        user_id = member.id
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

        text = build_milestone_text(hours, is_nl=is_nl, ask_testimonial=ask_testimonial)
        try:
            if with_opt_buttons:
                await member.send(text, view=ShoutoutOptView())
            else:
                await member.send(text)
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

    async def _maybe_shoutout(self, member: discord.Member, seconds: int) -> None:
        if not MILESTONE_ANNOUNCE_CHANNEL_ID:
            return
        hours = highest_shoutout(seconds)
        if hours is None:
            return
        guild_id = member.guild.id
        if not await self.repo.milestone_shoutouts_enabled(guild_id, member.id):
            return
        # Claim first: a restart or a second check can never post it twice.
        if not await self.repo.milestone_announcement_claim(guild_id, member.id, f"{hours}h", int(time.time())):
            return

        channel = self.bot.get_channel(MILESTONE_ANNOUNCE_CHANNEL_ID)
        try:
            if channel is None:
                channel = await self.bot.fetch_channel(MILESTONE_ANNOUNCE_CHANNEL_ID)
            message = await channel.send(
                shoutout_text(member.mention, hours),
                allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=[member]),
            )
            try:
                await message.add_reaction("👏")
            except Exception:
                log.warning("Milestones: could not add 👏 to shout-out message=%s", message.id)
            log.info("Milestones: shout-out posted user=%s hours=%s", member.id, hours)
        except Exception as e:
            if not self._announce_warned:
                log.warning("Milestones: can't post shout-outs in %s (%s)", MILESTONE_ANNOUNCE_CHANNEL_ID, e)
                self._announce_warned = True

    async def seed_shoutouts(self) -> int:
        """
        Once, at the first start with shout-outs: mark every member's current
        highest tier as done without posting, so the café isn't flooded with
        "just reached" posts for hours earned before this update.
        """
        if not self.role_guild_id:
            return 0
        if await self.repo.kv_get(self.role_guild_id, SHOUTOUTS_SEEDED_KV):
            return 0
        start = await self.ensure_start(self.role_guild_id)
        now = int(time.time())
        seeded = 0
        for user_id in await self.repo.users_with_voice_since(self.role_guild_id, start):
            seconds = await self.repo.user_voice_seconds_since(self.role_guild_id, user_id, start)
            hours = highest_shoutout(seconds)
            if hours and await self.repo.milestone_announcement_claim(self.role_guild_id, user_id, f"{hours}h", now, posted=False):
                seeded += 1
        await self.repo.kv_set(self.role_guild_id, SHOUTOUTS_SEEDED_KV, str(now))
        log.info("Milestones: seeded %s existing milestones (no posts)", seeded)
        return seeded

    async def sync_role(self, member: discord.Member, seconds: int) -> bool:
        """Give the highest milestone role reached and remove every other one. True if anything changed."""
        added, removed = await self._apply_role(member, target_role_id(seconds))
        return added or removed > 0

    async def _apply_role(self, member: discord.Member, target_id: int | None) -> tuple[bool, int]:
        """Returns (role added, number of roles removed)."""
        # Read the member's roles fresh from Discord. The local cache can lag a
        # second behind a role change, and acting on stale roles is how a
        # member ends up with two milestone roles.
        try:
            member = await member.guild.fetch_member(member.id)
        except Exception:
            pass
        configured = {rid for _t, _n, rid in MILESTONE_ROLES if rid}
        to_remove = [r for r in member.roles if r.id in configured and r.id != target_id]
        target = member.guild.get_role(target_id) if target_id else None
        added = False
        removed = 0
        if target is not None and target not in member.roles:
            try:
                await member.add_roles(target, reason="Voice milestone reached")
                added = True
                log.info("Milestones: role added user=%s role=%s", member.id, target.id)
            except Exception as e:
                log.warning("Milestones: could not add role=%s user=%s (%s)", target.id, member.id, e)
        for role in to_remove:
            try:
                await member.remove_roles(role, reason="Voice milestone: only the highest role stays")
                removed += 1
                log.info("Milestones: role removed user=%s role=%s", member.id, role.id)
            except Exception as e:
                log.warning("Milestones: could not remove role=%s user=%s (%s)", role.id, member.id, e)
        return added, removed

    async def cleanup_roles(self) -> tuple[int, int, int]:
        """Members holding 2+ milestone roles keep only their highest. Returns (checked, fixed, removed)."""
        guild = self.bot.get_guild(self.role_guild_id) if self.role_guild_id else None
        if guild is None:
            return 0, 0, 0
        configured = {rid for _t, _n, rid in MILESTONE_ROLES if rid}
        checked = fixed = removed = 0
        for member in list(guild.members):
            if member.bot:
                continue
            checked += 1
            held = [r for r in member.roles if r.id in configured]
            if len(held) < 2:
                continue
            keep = max(held, key=lambda r: _role_rank(r.id))
            _added, count = await self._apply_role(member, keep.id)
            if count:
                fixed += 1
                removed += count
        log.info("Milestones: role cleanup checked=%s fixed=%s removed=%s", checked, fixed, removed)
        return checked, fixed, removed

    async def backfill_roles(self) -> tuple[int, int]:
        """Give roles to everyone who already passed a threshold. Returns (checked, changed). No DMs."""
        if not self.role_guild_id:
            return 0, 0
        guild = self.bot.get_guild(self.role_guild_id)
        if guild is None:
            return 0, 0
        start = await self.ensure_start(self.role_guild_id)
        checked = changed = 0
        for user_id in await self.repo.users_with_voice_since(self.role_guild_id, start):
            member = guild.get_member(user_id)
            if member is None or member.bot:
                continue
            checked += 1
            seconds = await self.repo.user_voice_seconds_since(self.role_guild_id, user_id, start)
            if await self.sync_role(member, seconds):
                changed += 1
        log.info("Milestones: role backfill checked=%s changed=%s", checked, changed)
        return checked, changed

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
