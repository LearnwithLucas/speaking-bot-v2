from __future__ import annotations

import asyncio
import logging
import random
import time

import discord

from .tracker import EN_ENGAGEMENT_QUESTIONS, NL_ENGAGEMENT_QUESTIONS
from .tracker import VoiceTracker as BaseVoiceTracker

log = logging.getLogger("voice.community_tracker")

GENERAL_PROMPT_DELAY_SECONDS = 60 * 60
GENERAL_PROMPT_COOLDOWN_SECONDS = 60 * 60


class VoiceTracker(BaseVoiceTracker):
    """Voice tracker variant that avoids public per-person progress nudges."""

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
