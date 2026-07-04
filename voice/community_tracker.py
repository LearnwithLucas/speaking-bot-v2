from __future__ import annotations

import asyncio
import datetime as dt
import logging
import random
import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord

from utils.time import amsterdam_iso_week_key
from .tracker import EN_ENGAGEMENT_QUESTIONS, NL_ENGAGEMENT_QUESTIONS
from .tracker import VoiceTracker as BaseVoiceTracker

log = logging.getLogger("voice.community_tracker")

GENERAL_PROMPT_DELAY_SECONDS = 60 * 60
GENERAL_PROMPT_COOLDOWN_SECONDS = 60 * 60

EN_NEXT_STEPS = [
    "Tiny next step: try `/topics` once and answer just one question.",
    "Tiny next step: press the speaking partner button when you feel ready.",
    "Tiny next step: join voice for one sentence, then leave if that is enough.",
    "Tiny next step: use `/guide` if you want help choosing where to start.",
]

NL_NEXT_STEPS = [
    "Kleine volgende stap: probeer `/onderwerpen` en beantwoord een vraag.",
    "Kleine volgende stap: druk op de spreekpartnerknop als je eraan toe bent.",
    "Kleine volgende stap: kom in voice voor een zin. Daarna mag je gewoon weer weg.",
    "Kleine volgende stap: gebruik `/guide` als je wilt weten waar je kunt beginnen.",
]


def _amsterdam_week_start_epoch() -> int:
    try:
        tz = ZoneInfo("Europe/Amsterdam")
        now = dt.datetime.now(tz=tz)
    except ZoneInfoNotFoundError:
        now = dt.datetime.now()
    week_start = (now - dt.timedelta(days=now.weekday())).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    return int(week_start.timestamp())


def _format_duration(seconds: int) -> str:
    minutes = max(1, int((seconds / 60.0) + 0.5))
    if minutes < 60:
        return f"{minutes} minute" if minutes == 1 else f"{minutes} minutes"
    hours = minutes // 60
    remainder = minutes % 60
    if remainder == 0:
        return f"{hours} hour" if hours == 1 else f"{hours} hours"
    return f"{hours}h {remainder}m"


def _build_weekly_recap_message(*, seconds: int, is_nl: bool) -> str:
    if is_nl:
        if seconds >= 60:
            opener = f"Deze week was je ongeveer {_format_duration(seconds)} in voice. Mooi dat je geoefend hebt."
        else:
            opener = "Je bent deze week in voice geweest. Dat telt al."
        return (
            f"{opener}\n\n"
            "Geen scorebord, geen vergelijking. Gewoon een rustig teken dat je bent komen oefenen.\n\n"
            f"{random.choice(NL_NEXT_STEPS)}"
        )

    if seconds >= 60:
        opener = f"This week you spent about {_format_duration(seconds)} in voice. Nice work showing up."
    else:
        opener = "You joined voice this week. That counts already."
    return (
        f"{opener}\n\n"
        "No leaderboard, no comparison. Just a quiet note that you practiced.\n\n"
        f"{random.choice(EN_NEXT_STEPS)}"
    )


class VoiceTracker(BaseVoiceTracker):
    """Voice tracker variant that avoids public per-person progress nudges."""

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

            since_epoch = _amsterdam_week_start_epoch()
            seconds = await self.repo.user_voice_seconds_since(self.guild_id, uid, since_epoch)
            is_nl = self._is_nl_channel(member.voice.channel if member.voice else None)
            message = _build_weekly_recap_message(seconds=seconds, is_nl=is_nl)

            await self.repo.user_state_mark_weekly_dm(self.guild_id, uid, week_key, now_epoch)

            try:
                await member.send(message)
                log.info("Weekly recap DM sent user=%s week=%s", uid, week_key)
            except discord.Forbidden:
                log.info("Weekly recap DM blocked by user privacy settings user=%s week=%s", uid, week_key)
            except discord.HTTPException:
                log.exception("Weekly recap DM failed (HTTPException) user=%s week=%s", uid, week_key)
            except Exception:
                log.exception("Weekly recap DM failed user=%s week=%s", uid, week_key)

        finally:
            self._weekly_dm_inflight.discard(uid)

    def _schedule_encouragement(self, member: discord.Member, channel_id: int) -> None:
        if self._bot is None:
            return

        uid = member.id
        self._cancel_encouragement_task(uid)

        channel = self._bot.get_channel(channel_id)
        is_nl = self._is_nl_channel(channel)
        prompts = NL_ENGAGEMENT_QUESTIONS if is_nl else EN_ENGAGEMENT_QUESTIONS

        async def _job() -> None:
            try:
                await asyncio.sleep(GENERAL_PROMPT_DELAY_SECONDS)

                voice = member.voice
                if voice is None or voice.channel is None or voice.channel.id != channel_id:
                    return

                now = time.time()
                last = self._last_engagement_at.get(channel_id, 0)
                if now - last < GENERAL_PROMPT_COOLDOWN_SECONDS:
                    return

                vc = self._bot.get_channel(channel_id)
                if not isinstance(vc, discord.VoiceChannel):
                    return

                humans = [m for m in vc.members if not m.bot]
                if not humans:
                    return

                await vc.send(random.choice(prompts))
                self._last_engagement_at[channel_id] = now

            except asyncio.CancelledError:
                return
            except Exception:
                log.exception("General voice prompt task failed channel=%s", channel_id)

        self._pending_encouragement[uid] = asyncio.create_task(_job())
