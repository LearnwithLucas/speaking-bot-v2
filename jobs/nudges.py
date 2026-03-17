# jobs/nudges.py
import logging
import time
import random
import datetime as dt
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord
from discord.ext import tasks

from db.repo import Repo

log = logging.getLogger("jobs.nudges")

TZ_NAME = "Europe/Amsterdam"

# KV keys — English
NUDGE_LAST_POST_DATE_KEY = "nudge_last_post_date"
NUDGE_PINNED_MSG_ID_KEY = "nudge_pinned_message_id"
NUDGE_PINNED_AT_KEY = "nudge_pinned_at_epoch"

# KV keys — Dutch
NL_NUDGE_LAST_POST_DATE_KEY = "nudge_nl_last_post_date"
NL_NUDGE_PINNED_MSG_ID_KEY = "nudge_nl_pinned_message_id"
NL_NUDGE_PINNED_AT_KEY = "nudge_nl_pinned_at_epoch"

UNPIN_AFTER_SECONDS = 24 * 60 * 60

NL_ANNOUNCEMENTS_CHANNEL_ID = 1433384734196633600

# ---- English nudge messages ----
EN_NUDGE_MESSAGES = [
    "The voice channels are open. No agenda, no pressure. Just drop in if you feel like it.",
    "If you've been meaning to speak this week, today is a good day. The channels are open.",
    "Speaking practice doesn't have to be a big thing. One sentence is enough to start.",
    "The hardest part is usually just joining. After that it gets easier. Channels are open.",
    "No preparation needed. No performance required. Just a conversation, whenever you're ready.",
    "If you've been lurking, that's fine. But the voice channels are open if you want to try.",
    "You don't have to be fluent to join. You just have to show up.",
    "Short reminder: the speaking channels are open. Come as you are.",
]

# ---- Dutch nudge messages ----
NL_NUDGE_MESSAGES = [
    "De spraakkanalen zijn open. Geen agenda, geen druk. Kom gewoon langs als je zin hebt.",
    "Als je deze week wilde oefenen, is vandaag een goede dag. De kanalen zijn open.",
    "Spreekoefening hoeft geen groot ding te zijn. Een zin is genoeg om te beginnen.",
    "Het moeilijkste is meestal gewoon instappen. Daarna wordt het makkelijker. Kanalen zijn open.",
    "Geen voorbereiding nodig. Geen prestatie vereist. Gewoon een gesprek, wanneer je er klaar voor bent.",
    "Als je al een tijdje meekijkt, dat is prima. Maar de spraakkanalen zijn open als je het wilt proberen.",
    "Je hoeft niet vloeiend te zijn om mee te doen. Je hoeft alleen maar te komen.",
    "Korte herinnering: de spraakkanalen zijn open. Kom zoals je bent.",
]

DAY_MAP = {
    "MON": 0,
    "TUE": 1,
    "WED": 2,
    "THU": 3,
    "FRI": 4,
    "SAT": 5,
    "SUN": 6,
}


def _get_tz() -> ZoneInfo | None:
    try:
        return ZoneInfo(TZ_NAME)
    except ZoneInfoNotFoundError:
        log.warning(
            "Timezone '%s' not available (install 'tzdata' package to fix). Falling back to local system time.",
            TZ_NAME,
        )
        return None


def _pick_message(messages: list[str]) -> str:
    return random.choice(messages)


class NudgeJobs:
    """
    Scheduled nudge posts for English and Dutch servers.
    English: posts to announcements channel on configured days/time.
    Dutch: posts to NL announcements channel on same schedule.
    Both pin for 24h then auto-unpin.
    Messages rotate randomly so it never feels like the same bot message.
    """

    def __init__(
        self,
        bot: discord.Client,
        repo: Repo,
        guild_id: int,
        channel_id: int,
        *,
        nudge_days: str = "MON,FRI",
        nudge_time: str = "15:00",
        message: str | None = None,
        dutch_guild_id: int | None = None,
    ):
        self.bot = bot
        self.repo = repo
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.dutch_guild_id = dutch_guild_id

        # If a custom message is passed use it as the only EN message
        self._en_messages = [message.strip()] if message else EN_NUDGE_MESSAGES

        self._tz = _get_tz()

        parsed_days: set[int] = set()
        for part in (nudge_days or "").split(","):
            key = part.strip().upper()
            if key in DAY_MAP:
                parsed_days.add(DAY_MAP[key])
        self._nudge_days = parsed_days or {DAY_MAP["MON"], DAY_MAP["FRI"]}

        try:
            hh, mm = (nudge_time or "15:00").strip().split(":", 1)
            self._nudge_hour = int(hh)
            self._nudge_minute = int(mm)
            if not (0 <= self._nudge_hour <= 23 and 0 <= self._nudge_minute <= 59):
                raise ValueError("out of range")
        except Exception:
            log.warning("Invalid NUDGE_TIME=%r; falling back to 15:00", nudge_time)
            self._nudge_hour = 15
            self._nudge_minute = 0

        self._tick.start()
        self._unpin_check.start()

    async def _get_text_channel(self, channel_id: int) -> discord.TextChannel | None:
        ch = self.bot.get_channel(channel_id)
        if isinstance(ch, discord.TextChannel):
            return ch
        try:
            fetched = await self.bot.fetch_channel(channel_id)
            if isinstance(fetched, discord.TextChannel):
                return fetched
        except Exception:
            pass
        log.warning("Channel not found or not a text channel: %s", channel_id)
        return None

    def _now_local(self) -> dt.datetime:
        if self._tz is not None:
            return dt.datetime.now(tz=self._tz)
        return dt.datetime.now()

    async def _post_nudge(
        self,
        *,
        channel_id: int,
        guild_id: int,
        message: str,
        last_post_key: str,
        pinned_msg_key: str,
        pinned_at_key: str,
        date_key: str,
    ) -> None:
        last_posted = await self.repo.kv_get(guild_id, last_post_key)
        if last_posted == date_key:
            return

        ch = await self._get_text_channel(channel_id)
        if not ch:
            return

        try:
            sent = await ch.send(message)
        except Exception:
            log.exception("Failed to send nudge to channel=%s", channel_id)
            return

        await self.repo.kv_set(guild_id, last_post_key, date_key)
        log.info("Nudge posted channel=%s date=%s", channel_id, date_key)

        pinned_at = int(time.time())
        try:
            await sent.pin(reason="SpeakingBot: nudge (auto-unpin after 24h)")
            await self.repo.kv_set(guild_id, pinned_msg_key, str(sent.id))
            await self.repo.kv_set(guild_id, pinned_at_key, str(pinned_at))
            log.info("Nudge pinned message_id=%s", sent.id)
        except discord.Forbidden:
            log.warning("Missing pin permission in channel=%s", channel_id)
        except Exception:
            log.exception("Failed to pin nudge message_id=%s", sent.id)

    async def _unpin_nudge(
        self,
        *,
        guild_id: int,
        channel_id: int,
        pinned_msg_key: str,
        pinned_at_key: str,
    ) -> None:
        msg_id_raw = await self.repo.kv_get(guild_id, pinned_msg_key)
        pinned_at_raw = await self.repo.kv_get(guild_id, pinned_at_key)
        if not msg_id_raw or not pinned_at_raw:
            return

        try:
            msg_id = int(msg_id_raw)
            pinned_at = int(pinned_at_raw)
        except ValueError:
            await self.repo.kv_set(guild_id, pinned_msg_key, "")
            await self.repo.kv_set(guild_id, pinned_at_key, "")
            return

        if int(time.time()) - pinned_at < UNPIN_AFTER_SECONDS:
            return

        ch = await self._get_text_channel(channel_id)
        if not ch:
            return

        try:
            msg = await ch.fetch_message(msg_id)
        except Exception:
            await self.repo.kv_set(guild_id, pinned_msg_key, "")
            await self.repo.kv_set(guild_id, pinned_at_key, "")
            log.info("Pinned nudge not found; cleared KV message_id=%s", msg_id)
            return

        try:
            await msg.unpin(reason="SpeakingBot: auto-unpin after 24h")
            log.info("Nudge unpinned message_id=%s", msg_id)
        except discord.Forbidden:
            log.warning("Missing unpin permission in channel=%s", channel_id)
        except Exception:
            log.exception("Failed to unpin nudge message_id=%s", msg_id)
        finally:
            await self.repo.kv_set(guild_id, pinned_msg_key, "")
            await self.repo.kv_set(guild_id, pinned_at_key, "")

    @tasks.loop(minutes=1)
    async def _tick(self) -> None:
        now = self._now_local()

        if now.weekday() not in self._nudge_days:
            return
        if not (now.hour == self._nudge_hour and now.minute == self._nudge_minute):
            return

        date_key = now.date().isoformat()

        # English nudge
        await self._post_nudge(
            channel_id=self.channel_id,
            guild_id=self.guild_id,
            message=_pick_message(self._en_messages),
            last_post_key=NUDGE_LAST_POST_DATE_KEY,
            pinned_msg_key=NUDGE_PINNED_MSG_ID_KEY,
            pinned_at_key=NUDGE_PINNED_AT_KEY,
            date_key=date_key,
        )

        # Dutch nudge
        if self.dutch_guild_id:
            await self._post_nudge(
                channel_id=NL_ANNOUNCEMENTS_CHANNEL_ID,
                guild_id=self.dutch_guild_id,
                message=_pick_message(NL_NUDGE_MESSAGES),
                last_post_key=NL_NUDGE_LAST_POST_DATE_KEY,
                pinned_msg_key=NL_NUDGE_PINNED_MSG_ID_KEY,
                pinned_at_key=NL_NUDGE_PINNED_AT_KEY,
                date_key=date_key,
            )

    @_tick.before_loop
    async def _before_tick(self) -> None:
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=5)
    async def _unpin_check(self) -> None:
        await self._unpin_nudge(
            guild_id=self.guild_id,
            channel_id=self.channel_id,
            pinned_msg_key=NUDGE_PINNED_MSG_ID_KEY,
            pinned_at_key=NUDGE_PINNED_AT_KEY,
        )
        if self.dutch_guild_id:
            await self._unpin_nudge(
                guild_id=self.dutch_guild_id,
                channel_id=NL_ANNOUNCEMENTS_CHANNEL_ID,
                pinned_msg_key=NL_NUDGE_PINNED_MSG_ID_KEY,
                pinned_at_key=NL_NUDGE_PINNED_AT_KEY,
            )

    @_unpin_check.before_loop
    async def _before_unpin(self) -> None:
        await self.bot.wait_until_ready()