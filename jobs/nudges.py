# jobs/nudges.py
import logging
import time
import datetime as dt
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord
from discord.ext import tasks

from db.repo import Repo

log = logging.getLogger("jobs.nudges")

TZ_NAME = "Europe/Amsterdam"

# KV keys (stored in bot_kv table via repo.kv_get/kv_set)
NUDGE_LAST_POST_DATE_KEY = "nudge_last_post_date"  # YYYY-MM-DD (Amsterdam date if TZ available)
NUDGE_PINNED_MSG_ID_KEY = "nudge_pinned_message_id"
NUDGE_PINNED_AT_KEY = "nudge_pinned_at_epoch"

UNPIN_AFTER_SECONDS = 24 * 60 * 60  # 24h

DEFAULT_NUDGE_MESSAGE = (
    "👋 **Speak Now reminder**\n"
    "If you’ve been meaning to join voice, this is your gentle nudge.\n"
    "Start small: hop in, say hi, or just listen for a minute — no pressure."
)

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
    """
    Windows dev environments often lack IANA tzdata.
    If tzdata isn't available, return None and we'll fall back to local time.
    """
    try:
        return ZoneInfo(TZ_NAME)
    except ZoneInfoNotFoundError:
        log.warning(
            "Timezone '%s' not available (install 'tzdata' package to fix). Falling back to local system time.",
            TZ_NAME,
        )
        return None


class NudgeJobs:
    """
    Mon/Fri 15:00 (Europe/Amsterdam) nudge post (configurable via env through app.py).

    - Clock-based (restart-safe)
    - Pins message (best effort)
    - Unpins after 24h (best effort)

    Expectations:
      - app.py passes nudge_days and nudge_time (strings) or you keep defaults.
      - nudge_time format: "HH:MM" (24h)
      - nudge_days format: "MON,FRI"
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
    ):
        self.bot = bot
        self.repo = repo
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.message = (message or DEFAULT_NUDGE_MESSAGE).strip()

        self._tz = _get_tz()

        # Parse days
        parsed_days: set[int] = set()
        for part in (nudge_days or "").split(","):
            key = part.strip().upper()
            if key in DAY_MAP:
                parsed_days.add(DAY_MAP[key])
        # Safe default if misconfigured
        self._nudge_days = parsed_days or {DAY_MAP["MON"], DAY_MAP["FRI"]}

        # Parse time
        try:
            hh, mm = (nudge_time or "15:00").strip().split(":", 1)
            self._nudge_hour = int(hh)
            self._nudge_minute = int(mm)
            if not (0 <= self._nudge_hour <= 23 and 0 <= self._nudge_minute <= 59):
                raise ValueError("hour/minute out of range")
        except Exception:
            log.warning("Invalid NUDGE_TIME=%r; falling back to 15:00", nudge_time)
            self._nudge_hour = 15
            self._nudge_minute = 0

        self._tick.start()
        self._unpin_check.start()

    async def _get_text_channel(self) -> discord.TextChannel | None:
        ch = self.bot.get_channel(self.channel_id)
        if isinstance(ch, discord.TextChannel):
            return ch

        # Fallback to fetch (in case not cached)
        try:
            fetched = await self.bot.fetch_channel(self.channel_id)
            if isinstance(fetched, discord.TextChannel):
                return fetched
        except Exception:
            pass

        log.warning("Announcements channel not found or not a text channel: %s", self.channel_id)
        return None

    def _now_local(self) -> dt.datetime:
        # If tz is available, use Amsterdam-aware time.
        if self._tz is not None:
            return dt.datetime.now(tz=self._tz)
        # Fallback: naive local time (still lets bot run; schedule may be off if OS TZ differs)
        return dt.datetime.now()

    @tasks.loop(minutes=1)
    async def _tick(self) -> None:
        now = self._now_local()

        # Monday=0 ... Sunday=6
        if now.weekday() not in self._nudge_days:
            return

        if not (now.hour == self._nudge_hour and now.minute == self._nudge_minute):
            return

        date_key = now.date().isoformat()
        last_posted = await self.repo.kv_get(self.guild_id, NUDGE_LAST_POST_DATE_KEY)
        if last_posted == date_key:
            return  # already posted today

        ch = await self._get_text_channel()
        if not ch:
            return

        # Send the nudge
        try:
            sent = await ch.send(self.message)
        except Exception:
            log.exception("Failed to send nudge message to channel=%s", self.channel_id)
            return

        # Mark posted (restart-safe)
        await self.repo.kv_set(self.guild_id, NUDGE_LAST_POST_DATE_KEY, date_key)
        log.info(
            "Nudge posted for %s at %02d:%02d (%s)",
            date_key,
            self._nudge_hour,
            self._nudge_minute,
            TZ_NAME if self._tz else "local-time-fallback",
        )

        # Try to pin (best effort)
        pinned_at = int(time.time())
        try:
            await sent.pin(reason="SpeakingBot: nudge (auto-unpin after 24h)")
            await self.repo.kv_set(self.guild_id, NUDGE_PINNED_MSG_ID_KEY, str(sent.id))
            await self.repo.kv_set(self.guild_id, NUDGE_PINNED_AT_KEY, str(pinned_at))
            log.info("Nudge pinned message_id=%s", sent.id)
        except discord.Forbidden:
            log.warning("Missing permission to pin messages in channel=%s", self.channel_id)
        except Exception:
            log.exception("Failed to pin nudge message_id=%s", sent.id)

    @_tick.before_loop
    async def _before_tick(self) -> None:
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=5)
    async def _unpin_check(self) -> None:
        msg_id_raw = await self.repo.kv_get(self.guild_id, NUDGE_PINNED_MSG_ID_KEY)
        pinned_at_raw = await self.repo.kv_get(self.guild_id, NUDGE_PINNED_AT_KEY)
        if not msg_id_raw or not pinned_at_raw:
            return

        try:
            msg_id = int(msg_id_raw)
            pinned_at = int(pinned_at_raw)
        except ValueError:
            # Corrupt KV; clear to stop looping
            await self.repo.kv_set(self.guild_id, NUDGE_PINNED_MSG_ID_KEY, "")
            await self.repo.kv_set(self.guild_id, NUDGE_PINNED_AT_KEY, "")
            return

        if int(time.time()) - pinned_at < UNPIN_AFTER_SECONDS:
            return

        ch = await self._get_text_channel()
        if not ch:
            return

        try:
            msg = await ch.fetch_message(msg_id)
        except Exception:
            # Message gone or inaccessible; clear KV
            await self.repo.kv_set(self.guild_id, NUDGE_PINNED_MSG_ID_KEY, "")
            await self.repo.kv_set(self.guild_id, NUDGE_PINNED_AT_KEY, "")
            log.info("Pinned nudge message not found; cleared KV message_id=%s", msg_id)
            return

        try:
            await msg.unpin(reason="SpeakingBot: auto-unpin after 24h")
            log.info("Nudge unpinned message_id=%s", msg_id)
        except discord.Forbidden:
            log.warning("Missing permission to unpin messages in channel=%s", self.channel_id)
        except Exception:
            log.exception("Failed to unpin nudge message_id=%s", msg_id)
        finally:
            # Clear KV regardless to avoid repeated attempts forever
            await self.repo.kv_set(self.guild_id, NUDGE_PINNED_MSG_ID_KEY, "")
            await self.repo.kv_set(self.guild_id, NUDGE_PINNED_AT_KEY, "")

    @_unpin_check.before_loop
    async def _before_unpin(self) -> None:
        await self.bot.wait_until_ready()
