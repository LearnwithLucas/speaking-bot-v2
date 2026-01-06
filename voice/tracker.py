import asyncio
import time
import logging
from typing import Dict, Optional, Tuple

import discord

from db.repo import Repo
from utils.time import amsterdam_iso_week_key, amsterdam_day_key, amsterdam_day_key_from_epoch
from .rules import is_in_speak_now_category, should_count_state, qualifies_first_voice_attempt

log = logging.getLogger("voice.tracker")

"""
Achievements intentionally do not reward duration, frequency, or volume.
They exist to mark courage moments, not progress.

Guardrails:
- Private only (no public messaging)
- No streaks / sequences / escalation
- At most ONE achievement awarded per join event (prevents reinforcement spikes)
"""

# Existing
ACH_FIRST_VOICE_ATTEMPT = "first_voice_attempt"
FIRST_VOICE_ATTEMPT_CHECK_SECONDS = 180  # 3 minutes

# New approved achievements
ACH_JOINED_AGAIN = "joined_again"
ACH_CAME_BACK_AFTER_BREAK = "came_back_after_break"
ACH_SPOKE_WITH_SOMEONE_NEW = "spoke_with_someone_new"

# Joined-again reconnection cooldown (prevents false positives on hiccups / quick reconnects)
JOINED_AGAIN_MIN_GAP_SECONDS = 30 * 60  # 30 minutes

# Came back after break threshold
BREAK_MIN_DAYS = 14
BREAK_MIN_SECONDS = BREAK_MIN_DAYS * 86400

# Spoke-with-new guardrail: avoid crowded-room mass awarding (applies to ANY qualifying channel)
MAX_NEW_MEET_ROOM_SIZE = 4

WEEKLY_DM_MESSAGE = (
    "👋 Hey! Noticed you hopped into voice this week — nice.\n"
    "If you feel like speaking, start tiny: one sentence is enough. No pressure."
)

INACTIVITY_MIN_DAYS = 14
INACTIVITY_COOLDOWN_DAYS = 30
NO_NUDGE_AFTER_SPEAK_SECONDS = 72 * 3600

INACTIVITY_MSG_A = (
    "If you ever feel like joining a table again, you don’t need to catch up or explain anything. You can just join."
)
INACTIVITY_MSG_B = (
    "No pressure to be consistent here. If you want to speak again sometime, you can just join and leave whenever."
)


class VoiceTracker:
    def __init__(
        self,
        repo: Repo,
        guild_id: int,
        speak_now_category_id: int,
        enable_inactivity_nudge: bool,
        inactivity_variant: str,
        afk_channel_id: int | None = None,
    ):
        self.repo = repo
        self.guild_id = guild_id
        self.speak_now_category_id = speak_now_category_id
        self.afk_channel_id = afk_channel_id

        self.active: Dict[int, Tuple[int, int]] = {}
        self._pending_first_attempt: Dict[int, asyncio.Task] = {}
        self._weekly_dm_inflight: set[int] = set()

        self.enable_inactivity_nudge = enable_inactivity_nudge
        self.inactivity_variant = inactivity_variant

    def _is_afk_channel(self, guild: discord.Guild, channel: Optional[discord.abc.GuildChannel]) -> bool:
        if channel is None:
            return False

        # Prefer explicit AFK_CHANNEL_ID (works even if guild AFK isn't configured correctly)
        if self.afk_channel_id is not None:
            return bool(getattr(channel, "id", None) == self.afk_channel_id)

        # Fallback to Discord server AFK channel setting
        afk = getattr(guild, "afk_channel", None)
        return bool(afk and afk.id == getattr(channel, "id", None))

    def _is_target_voice_channel(self, guild: discord.Guild, channel) -> bool:
        if channel is None:
            return False
        if not is_in_speak_now_category(channel, self.speak_now_category_id):
            return False
        if self._is_afk_channel(guild, channel):
            return False
        return True

    def _cancel_first_attempt_task(self, user_id: int) -> None:
        task = self._pending_first_attempt.pop(user_id, None)
        if task and not task.done():
            task.cancel()

    def _schedule_first_attempt_check(self, member: discord.Member, channel_id: int, started_at: int) -> None:
        uid = member.id
        self._cancel_first_attempt_task(uid)

        async def _job():
            try:
                await asyncio.sleep(FIRST_VOICE_ATTEMPT_CHECK_SECONDS)

                voice = member.voice
                if voice is None or voice.channel is None:
                    return
                if voice.channel.id != channel_id:
                    return
                if not self._is_target_voice_channel(member.guild, voice.channel):
                    return
                if not qualifies_first_voice_attempt(voice):
                    return

                newly_awarded = await self.repo.achievement_award_once(
                    guild_id=self.guild_id,
                    user_id=uid,
                    achievement_id=ACH_FIRST_VOICE_ATTEMPT,
                    earned_at=int(time.time()),
                )
                if newly_awarded:
                    log.info("Achievement awarded: %s user=%s", ACH_FIRST_VOICE_ATTEMPT, uid)

            except asyncio.CancelledError:
                return
            except Exception:
                log.exception("First voice attempt check failed for user=%s", uid)

        self._pending_first_attempt[uid] = asyncio.create_task(_job())

    async def _maybe_send_weekly_dm(self, member: discord.Member, now_epoch: int) -> None:
        uid = member.id
        if uid in self._weekly_dm_inflight:
            return

        self._weekly_dm_inflight.add(uid)
        try:
            week_key = amsterdam_iso_week_key()

            state = await self.repo.user_state_get(self.guild_id, uid)
            last_week = state["last_weekly_dm_week"] if state else None
            if last_week == week_key:
                return

            await self.repo.user_state_mark_weekly_dm(self.guild_id, uid, week_key, now_epoch)

            try:
                await member.send(WEEKLY_DM_MESSAGE)
                log.info("Weekly DM sent user=%s week=%s", uid, week_key)
            except discord.Forbidden:
                log.info("Weekly DM blocked by user privacy settings user=%s week=%s", uid, week_key)
            except discord.HTTPException:
                log.exception("Weekly DM failed (HTTPException) user=%s week=%s", uid, week_key)
            except Exception:
                log.exception("Weekly DM failed user=%s week=%s", uid, week_key)

        finally:
            self._weekly_dm_inflight.discard(uid)

    async def _maybe_send_inactivity_dm(self, member: discord.Member, now: int) -> None:
        if not self.enable_inactivity_nudge:
            return

        state = await self.repo.user_state_get(self.guild_id, member.id)
        if not state or not state.get("last_voice_join_at"):
            return

        last_join = int(state["last_voice_join_at"])
        last_nudge = state.get("last_inactivity_nudge_at")
        last_nudge = int(last_nudge) if last_nudge else None

        if now - last_join < INACTIVITY_MIN_DAYS * 86400:
            return
        if now - last_join < NO_NUDGE_AFTER_SPEAK_SECONDS:
            return
        if last_nudge and now - last_nudge < INACTIVITY_COOLDOWN_DAYS * 86400:
            return

        message = INACTIVITY_MSG_B if self.inactivity_variant == "B" else INACTIVITY_MSG_A

        await self.repo.user_state_mark_inactivity_nudge(self.guild_id, member.id, now)

        try:
            await member.send(message)
            log.info("Inactivity DM sent user=%s", member.id)
        except discord.Forbidden:
            log.info("Inactivity DM blocked by privacy user=%s", member.id)
        except Exception:
            log.exception("Inactivity DM failed user=%s", member.id)

    # -------------------------
    # Achievements (join-time; max 1 per join)
    # Priority:
    #   1) first_voice_attempt (handled separately; if not earned, suppress join-time awards)
    #   2) came_back_after_break
    #   3) joined_again
    #   4) spoke_with_someone_new
    # -------------------------
    async def _maybe_award_join_achievement(self, member: discord.Member, after_channel: discord.VoiceChannel, now: int) -> None:
        uid = member.id

        # Suppress join-time achievements until "first voice" is earned.
        has_first = await self.repo.achievement_has(self.guild_id, uid, ACH_FIRST_VOICE_ATTEMPT)
        if not has_first:
            return

        state = await self.repo.user_state_get(self.guild_id, uid)
        prev_last_join = int(state["last_voice_join_at"]) if state and state.get("last_voice_join_at") else None

        awarded = False

        # 1) Came back after a break (award on join; no time threshold)
        if not awarded and prev_last_join is not None:
            if now - prev_last_join >= BREAK_MIN_SECONDS:
                if not await self.repo.achievement_has(self.guild_id, uid, ACH_CAME_BACK_AFTER_BREAK):
                    if await self.repo.achievement_award_once(self.guild_id, uid, ACH_CAME_BACK_AFTER_BREAK, now):
                        log.info("Achievement awarded: %s user=%s", ACH_CAME_BACK_AFTER_BREAK, uid)
                        awarded = True

        # 2) Joined again (new Amsterdam day) with reconnection cooldown guardrail
        if not awarded and prev_last_join is not None:
            prev_day = amsterdam_day_key_from_epoch(prev_last_join)
            today = amsterdam_day_key()
            if prev_day != today and (now - prev_last_join) >= JOINED_AGAIN_MIN_GAP_SECONDS:
                if not await self.repo.achievement_has(self.guild_id, uid, ACH_JOINED_AGAIN):
                    if await self.repo.achievement_award_once(self.guild_id, uid, ACH_JOINED_AGAIN, now):
                        log.info("Achievement awarded: %s user=%s", ACH_JOINED_AGAIN, uid)
                        awarded = True

        # 3) Spoke with someone new (joining member only), with room-size guardrail
        if not awarded:
            # Only evaluate in small groups to prevent noisy/crowded-room awarding.
            humans = [m for m in after_channel.members if not m.bot]
            if len(humans) <= MAX_NEW_MEET_ROOM_SIZE:
                for other in humans:
                    if other.id == uid:
                        continue
                    is_new_pair = await self.repo.voice_met_add_if_new_pair(self.guild_id, uid, other.id, now)
                    if is_new_pair:
                        if not await self.repo.achievement_has(self.guild_id, uid, ACH_SPOKE_WITH_SOMEONE_NEW):
                            if await self.repo.achievement_award_once(self.guild_id, uid, ACH_SPOKE_WITH_SOMEONE_NEW, now):
                                log.info("Achievement awarded: %s user=%s other=%s", ACH_SPOKE_WITH_SOMEONE_NEW, uid, other.id)
                        awarded = True
                        break

    # -------------------------
    # Bootstrap / events
    # -------------------------
    async def bootstrap_from_guild(self, guild: discord.Guild) -> None:
        now = int(time.time())

        for vc in guild.voice_channels:
            for member in vc.members:
                await self.repo.end_open_session(self.guild_id, member.id, ended_at=now)

        # Start sessions for users currently in target category and not self-deafened
        # NOTE: no weekly DM, no inactivity DM, no join-achievements during bootstrap.
        for vc in guild.voice_channels:
            if not self._is_target_voice_channel(guild, vc):
                continue
            for member in vc.members:
                if member.bot:
                    continue

                await self.repo.user_state_touch_voice_join(self.guild_id, member.id, now)

                if not should_count_state(member.voice):
                    continue
                await self._start(member.id, vc.id, now)

                self._schedule_first_attempt_check(member, vc.id, now)

        log.info("Bootstrap complete. Active sessions: %s", len(self.active))

    async def handle_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        if member.bot:
            return

        uid = member.id
        now = int(time.time())

        before_channel = before.channel
        after_channel = after.channel

        before_in_target = self._is_target_voice_channel(member.guild, before_channel)
        after_in_target = self._is_target_voice_channel(member.guild, after_channel)

        # Entering target voice: evaluate inactivity + achievements using PREVIOUS state, then update state.
        if not before_in_target and after_in_target and after_channel is not None:
            # Step 6 (gated)
            await self._maybe_send_inactivity_dm(member, now)

            # Achievements (join-time, max 1 per join)
            await self._maybe_award_join_achievement(member, after_channel, now)

            # Record join (this becomes the new last_voice_join_at)
            await self.repo.user_state_touch_voice_join(self.guild_id, uid, now)

            # Schedule first voice attempt check
            self._schedule_first_attempt_check(member, after_channel.id, now)

            # Weekly DM check
            await self._maybe_send_weekly_dm(member, now)

        # Cancel pending first-attempt checks if they leave target voice or move away.
        if before_in_target and not after_in_target:
            self._cancel_first_attempt_task(uid)
        elif before_in_target and after_in_target and before_channel and after_channel and before_channel.id != after_channel.id:
            self._cancel_first_attempt_task(uid)
            await self.repo.user_state_touch_voice_join(self.guild_id, uid, now)
            self._schedule_first_attempt_check(member, after_channel.id, now)

        # Existing "counted minutes" logic (unchanged)
        before_counts = before_in_target and should_count_state(before)
        after_counts = after_in_target and should_count_state(after)

        if before_counts and not after_counts:
            await self._end(uid, now)
            return

        if not before_counts and after_counts and after_channel is not None:
            await self._start(uid, after_channel.id, now)
            return

        if before_counts and after_counts and before_channel and after_channel and before_channel.id != after_channel.id:
            await self._end(uid, now)
            await self._start(uid, after_channel.id, now)
            return

    async def _start(self, user_id: int, channel_id: int, started_at: int) -> None:
        self.active[user_id] = (channel_id, started_at)
        await self.repo.start_session(self.guild_id, user_id, channel_id, started_at)
        log.debug("Start session user=%s channel=%s", user_id, channel_id)

    async def _end(self, user_id: int, ended_at: int) -> None:
        self.active.pop(user_id, None)
        await self.repo.end_open_session(self.guild_id, user_id, ended_at)
        log.debug("End session user=%s", user_id)

    async def shutdown(self) -> None:
        for uid in list(self._pending_first_attempt.keys()):
            self._cancel_first_attempt_task(uid)
