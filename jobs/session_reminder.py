from __future__ import annotations

# jobs/session_reminder.py
import logging
import datetime as dt
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord
from discord.ext import tasks

from db.repo import Repo

log = logging.getLogger("jobs.session_reminder")

TZ_NAME = "Europe/Amsterdam"

# ---- Channel IDs ----
SS_CHANNEL_ID = 1476127448562139166   # supported-speaking
OS_CHANNEL_ID = 1481647973640310814   # ondersteund-spreken

# ---- Role IDs ----
SS_ROLE_ID = 1476129292185370735      # @Supported Speaker
OS_ROLE_ID = 1448690000836296835      # @Ondersteund Spreken

# ---- KV keys (prevent double-posting on restart) ----
KV_SS_LAST_REMINDER = "ss_session_reminder_last"
KV_OS_LAST_REMINDER = "os_session_reminder_last"

# ---- Schedule ----
# OS: every Monday at 18:30 Amsterdam time (session at 19:00)
OS_WEEKDAY = 0        # Monday
OS_HOUR = 18
OS_MINUTE = 30

# SS: every Saturday at 14:00 Amsterdam time (session at 14:30)
# Active from April 5, 2026 onwards (first Saturday on or after April 5)
SS_WEEKDAY = 5        # Saturday
SS_HOUR = 14
SS_MINUTE = 0
SS_START_DATE = dt.date(2026, 4, 5)


def _get_tz() -> ZoneInfo | None:
    try:
        return ZoneInfo(TZ_NAME)
    except ZoneInfoNotFoundError:
        log.warning("SessionReminder: timezone '%s' not available, falling back to UTC.", TZ_NAME)
        return None


class SessionReminderJob:
    def __init__(
        self,
        *,
        bot: discord.Client,
        repo: Repo,
        guild_id: int,
        dutch_guild_id: int | None = None,
    ) -> None:
        self._bot = bot
        self._repo = repo
        self._guild_id = guild_id
        self._dutch_guild_id = dutch_guild_id
        self._tz = _get_tz()
        self._tick.start()

    def _now(self) -> dt.datetime:
        return dt.datetime.now(tz=self._tz or ZoneInfo("UTC"))

    async def _get_channel(self, channel_id: int) -> discord.TextChannel | None:
        ch = self._bot.get_channel(channel_id)
        if isinstance(ch, discord.TextChannel):
            return ch
        try:
            fetched = await self._bot.fetch_channel(channel_id)
            if isinstance(fetched, discord.TextChannel):
                return fetched
        except Exception:
            pass
        log.warning("SessionReminder: could not fetch channel %s", channel_id)
        return None

    @tasks.loop(minutes=1)
    async def _tick(self) -> None:
        now = self._now()
        date_str = now.date().isoformat()
        slot_key = f"{date_str}:{now.hour:02d}:{now.minute:02d}"

        # OS reminder — every Monday 18:30 Amsterdam
        if (
            now.weekday() == OS_WEEKDAY
            and now.hour == OS_HOUR
            and now.minute == OS_MINUTE
        ):
            last = await self._repo.kv_get(
                self._dutch_guild_id or self._guild_id, KV_OS_LAST_REMINDER
            )
            if last != slot_key:
                await self._send_os_reminder()
                await self._repo.kv_set(
                    self._dutch_guild_id or self._guild_id,
                    KV_OS_LAST_REMINDER,
                    slot_key,
                )

        # SS reminder — every Saturday 14:00 Amsterdam, from SS_START_DATE onwards
        if (
            now.weekday() == SS_WEEKDAY
            and now.hour == SS_HOUR
            and now.minute == SS_MINUTE
            and now.date() >= SS_START_DATE
        ):
            last = await self._repo.kv_get(self._guild_id, KV_SS_LAST_REMINDER)
            if last != slot_key:
                await self._send_ss_reminder()
                await self._repo.kv_set(self._guild_id, KV_SS_LAST_REMINDER, slot_key)

    @_tick.before_loop
    async def _before(self) -> None:
        await self._bot.wait_until_ready()

    async def _send_os_reminder(self) -> None:
        ch = await self._get_channel(OS_CHANNEL_ID)
        if not ch:
            return
        try:
            await ch.send(
                f"<@&{OS_ROLE_ID}>\n\n"
                "De live sessie begint over 30 minuten. Om 19:00 CET zijn we live.\n\n"
                "Het spreekonderwerp van vandaag heb je gisteren ontvangen. "
                "Je hoeft je niet voor te bereiden, maar als je dat hebt gedaan, "
                "is dat helemaal prima.\n\n"
                "Tot zo!"
            )
            log.info("SessionReminder: OS reminder sent")
        except Exception:
            log.exception("SessionReminder: failed to send OS reminder")

    async def _send_ss_reminder(self) -> None:
        ch = await self._get_channel(SS_CHANNEL_ID)
        if not ch:
            return
        try:
            await ch.send(
                f"<@&{SS_ROLE_ID}>\n\n"
                "The live speaking session starts in 30 minutes. We go live at 14:30 CET.\n\n"
                "No preparation needed. Just show up and speak. "
                "One sentence is enough to get started.\n\n"
                "See you there!"
            )
            log.info("SessionReminder: SS reminder sent")
        except Exception:
            log.exception("SessionReminder: failed to send SS reminder")
