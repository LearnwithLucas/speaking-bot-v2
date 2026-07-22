from __future__ import annotations

import datetime as dt
import logging
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord
from discord.ext import tasks

from commands.chat_jerry import ChatJerryPublisher

log = logging.getLogger("jobs.daily_questions")

TZ_NAME = "Europe/Amsterdam"
POST_HOUR = 9
POST_MINUTE = 0


def _get_tz() -> ZoneInfo | None:
    try:
        return ZoneInfo(TZ_NAME)
    except ZoneInfoNotFoundError:
        log.warning("Timezone '%s' not available. Falling back to local system time.", TZ_NAME)
        return None


class DailyQuestionJob:
    def __init__(
        self,
        *,
        bot: discord.Client,
        publisher: ChatJerryPublisher,
        en_guild_id: int,
        nl_guild_id: int | None = None,
    ) -> None:
        self._bot = bot
        self._publisher = publisher
        self._en_guild_id = en_guild_id
        self._nl_guild_id = nl_guild_id
        self._tz = _get_tz()
        self._tick.start()

    def _now(self) -> dt.datetime:
        if self._tz is not None:
            return dt.datetime.now(tz=self._tz)
        return dt.datetime.now()

    @tasks.loop(minutes=1)
    async def _tick(self) -> None:
        now = self._now()
        if not (now.hour == POST_HOUR and now.minute == POST_MINUTE):
            return

        date_key = now.date().isoformat()
        await self._publisher.publish_daily_question(
            self._en_guild_id,
            is_nl=False,
            date_key=date_key,
        )
        if self._nl_guild_id:
            await self._publisher.publish_daily_question(
                self._nl_guild_id,
                is_nl=True,
                date_key=date_key,
            )

    @_tick.before_loop
    async def _before_tick(self) -> None:
        await self._bot.wait_until_ready()
