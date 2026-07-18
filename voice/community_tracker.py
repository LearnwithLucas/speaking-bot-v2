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

STAY_PROMPT_COOLDOWN_SECONDS = 10 * 60
STAY_PROMPT_VIEW_TIMEOUT_SECONDS = 10 * 60
WEEKLY_RECAP_DM_DELAY_SECONDS = 5 * 60
GENERAL_PROMPT_DELAY_SECONDS = 60 * 60
GENERAL_PROMPT_COOLDOWN_SECONDS = 60 * 60

STAY_DURATION_OPTIONS: tuple[tuple[int, str, str], ...] = (
    (15 * 60, "15 min", "15 min"),
    (30 * 60, "30 min", "30 min"),
    (45 * 60, "45 min", "45 min"),
    (60 * 60, "1 hour", "1 uur"),
    (2 * 60 * 60, "2 hours", "2 uur"),
    (3 * 60 * 60, "3 hours", "3 uur"),
)

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


def _format_duration(seconds: int, *, is_nl: bool) -> str:
    minutes = max(1, int((seconds / 60.0) + 0.5))
    if minutes < 60:
        if is_nl:
            return "1 minuut" if minutes == 1 else f"{minutes} minuten"
        return "1 minute" if minutes == 1 else f"{minutes} minutes"

    hours = minutes // 60
    remainder = minutes % 60
    if remainder == 0:
        if is_nl:
            return "1 uur" if hours == 1 else f"{hours} uur"
        return "1 hour" if hours == 1 else f"{hours} hours"
    return f"{hours}h {remainder}m"


def _build_weekly_recap_message(*, seconds: int, is_nl: bool) -> str:
    if is_nl:
        if seconds >= 60:
            opener = f"Deze week was je ongeveer {_format_duration(seconds, is_nl=True)} in voice. Mooi dat je geoefend hebt."
        else:
            opener = "Je bent deze week in voice geweest. Dat telt al."
        return (
            f"{opener}\n\n"
            "Ik stuur dit pas na je eerste 5 minuten, zodat het geen druk geeft zodra je binnenkomt.\n"
            "Geen scorebord, geen vergelijking. Gewoon fijn dat je bent komen oefenen.\n\n"
            "Tip: gebruik de vraag in het voice-kanaal om te laten zien hoelang je blijft, "
            "dan kunnen anderen je makkelijker vinden in op-zoek-naar-een-partner."
        )

    if seconds >= 60:
        opener = f"This week you spent about {_format_duration(seconds, is_nl=False)} in voice. Nice work showing up."
    else:
        opener = "You joined voice this week. That counts already."
    return (
        f"{opener}\n\n"
        "I wait until you have been here 5 minutes before sending this, so it does not jump on you right away.\n"
        "No leaderboard, no comparison. Just glad you came to practice.\n\n"
        "Tip: use the question in the voice chat to share how long you are staying, "
        "then people can find you more easily in looking-for-a-partner."
    )


class StayDurationButton(discord.ui.Button):
    def __init__(self, *, seconds: int, label: str, row: int) -> None:
        super().__init__(label=label, style=discord.ButtonStyle.secondary, row=row)
        self.seconds = seconds

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, StayDurationView):
            await interaction.response.send_message("This button is not ready. Try the partner channel instead.", ephemeral=True)
            return
        await view.mark_available(interaction, duration_seconds=self.seconds)


class StayDurationView(discord.ui.View):
    def __init__(self, *, target_user_id: int, is_nl: bool) -> None:
        super().__init__(timeout=STAY_PROMPT_VIEW_TIMEOUT_SECONDS)
        self.target_user_id = target_user_id
        self.is_nl = is_nl

        for index, (seconds, en_label, nl_label) in enumerate(STAY_DURATION_OPTIONS):
            self.add_item(
                StayDurationButton(
                    seconds=seconds,
                    label=nl_label if is_nl else en_label,
                    row=0 if index < 3 else 1,
                )
            )

    async def mark_available(self, interaction: discord.Interaction, *, duration_seconds: int) -> None:
        if interaction.user.id != self.target_user_id:
            msg = (
                "Deze vraag was voor de persoon die net binnenkwam. Gebruik de partnerknoppen als jij ook vrij bent."
                if self.is_nl
                else "This question was for the person who just joined. Use the partner buttons if you are free too."
            )
            await interaction.response.send_message(msg, ephemeral=True)
            return

        finder = getattr(interaction.client, "_partner_finder", None)
        if finder is None:
            msg = "Partnerzoeker is nog niet klaar. Probeer het zo nog eens." if self.is_nl else "Partner finder is not ready yet. Try again in a moment."
            await interaction.response.send_message(msg, ephemeral=True)
            return

        await finder.mark_available(
            user=interaction.user,
            guild=interaction.guild,
            interaction=interaction,
            duration_seconds=duration_seconds,
            is_nl=self.is_nl,
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
                self._weekly_dm_inflight.discard(uid)
                return

            voice = member.voice
            channel_id = voice.channel.id if voice and voice.channel else None
            is_nl = self._is_nl_channel(voice.channel if voice else None)

            asyncio.create_task(
                self._send_weekly_recap_dm_after_delay(
                    member=member,
                    week_key=week_key,
                    channel_id=channel_id,
                    is_nl=is_nl,
                )
            )
            log.info("Weekly recap DM scheduled user=%s week=%s delay=%s", uid, week_key, WEEKLY_RECAP_DM_DELAY_SECONDS)
        except Exception:
            self._weekly_dm_inflight.discard(uid)
            raise

    async def _send_weekly_recap_dm_after_delay(
        self,
        *,
        member: discord.Member,
        week_key: str,
        channel_id: int | None,
        is_nl: bool,
    ) -> None:
        uid = member.id
        try:
            await asyncio.sleep(WEEKLY_RECAP_DM_DELAY_SECONDS)

            voice = member.voice
            if channel_id is None or voice is None or voice.channel is None or voice.channel.id != channel_id:
                log.info("Weekly recap DM skipped; user left before delay user=%s week=%s", uid, week_key)
                return

            state = await self.repo.user_state_get(self.guild_id, uid)
            last_week = state["last_weekly_dm_week"] if state else None
            if last_week == week_key:
                return

            since_epoch = _amsterdam_week_start_epoch()
            seconds = await self.repo.user_voice_seconds_since(self.guild_id, uid, since_epoch)
            message = _build_weekly_recap_message(seconds=seconds, is_nl=is_nl)

            await self.repo.user_state_mark_weekly_dm(self.guild_id, uid, week_key, int(time.time()))

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
        asyncio.create_task(self._ask_expected_stay(member, channel_id))

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

    async def _ask_expected_stay(self, member: discord.Member, channel_id: int) -> None:
        try:
            if self._bot is None:
                return

            uid = member.id
            prompt_times = getattr(self, "_last_stay_prompt_at", None)
            if prompt_times is None:
                prompt_times = {}
                setattr(self, "_last_stay_prompt_at", prompt_times)

            now = time.time()
            if now - prompt_times.get(uid, 0) < STAY_PROMPT_COOLDOWN_SECONDS:
                return

            vc = self._bot.get_channel(channel_id)
            if not isinstance(vc, discord.VoiceChannel):
                return

            voice = member.voice
            if voice is None or voice.channel is None or voice.channel.id != channel_id:
                return

            is_nl = self._is_nl_channel(vc)
            content = (
                f"<@{uid}> hoelang denk je dat je hier blijft?"
                if is_nl
                else f"<@{uid}> how long do you think you'll be here?"
            )
            await vc.send(
                content,
                view=StayDurationView(target_user_id=uid, is_nl=is_nl),
                allowed_mentions=discord.AllowedMentions(users=True),
            )
            prompt_times[uid] = now
        except (discord.Forbidden, discord.HTTPException):
            log.info("Stay duration prompt could not be sent user=%s channel=%s", member.id, channel_id)
        except Exception:
            log.exception("Stay duration prompt failed user=%s channel=%s", member.id, channel_id)
