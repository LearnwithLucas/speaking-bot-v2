from __future__ import annotations

# jobs/weekly_tip.py
#
# Every Monday at 12:00 Amsterdam time, one tip in #announcements (EN server).
# No pings. Tips rotate in order; the last index is stored, so restarts never
# repeat or skip a tip.

import datetime as dt
import logging
import time
from typing import Any
from zoneinfo import ZoneInfo

import discord
from discord.ext import tasks

log = logging.getLogger("jobs.weekly_tip")

TZ = ZoneInfo("Europe/Amsterdam")
POST_WEEKDAY = 0  # Monday
POST_TIME = dt.time(12, 0)

KV_LAST_INDEX = "weekly_tip_last_index"
KV_LAST_POSTED = "weekly_tip_last_posted"   # "YYYY-MM-DD|epoch|index"

TIPS: tuple[tuple[str, str], ...] = (
    ("Café Hour", "Every day at 19:00 Amsterdam time, learners meet in Open Conversation. Check Events for your local time."),
    ("Partner finder", "Looking for a partner? Go to #looking-for-a-partner, choose when you're free, and the bot matches you with someone at your level."),
    ("Speaking Ping", "Want to know when people are talking? Go to Channels & Roles and choose 'Yes, ping me'."),
    ("/profile", "Type /profile to see your speaking time and achievements. Only you can see it, unless you press Share."),
    ("CAFE tag", "Wear the CAFE tag next to your name: open your profile, choose Server Tag, then Online English Café."),
    ("Say hello", "New here? Say hi in #chat-in-english. Everybody started where you are."),
    ("Full tables", "Is a table full? Press 'Knock on a full table' in #looking-for-a-partner to ask if you can join."),
)


def tip_text(index: int) -> str:
    title, body = TIPS[index]
    return f"💡 **Tip of the week: {title}**\n{body}"


class WeeklyTip:
    def __init__(self, *, bot: discord.Client, repo: Any, guild_id: int, channel_id: int) -> None:
        self.bot = bot
        self.repo = repo
        self.guild_id = guild_id
        self.channel_id = channel_id
        self._tick.start()

    async def _last_index(self) -> int:
        raw = await self.repo.kv_get(self.guild_id, KV_LAST_INDEX)
        try:
            return int(raw)
        except (TypeError, ValueError):
            return -1

    async def next_index(self) -> int:
        return (await self._last_index() + 1) % len(TIPS)

    async def last_posted(self) -> tuple[str, int, int] | None:
        raw = await self.repo.kv_get(self.guild_id, KV_LAST_POSTED)
        try:
            day, epoch, index = raw.split("|")
            return day, int(epoch), int(index)
        except Exception:
            return None

    @tasks.loop(minutes=1)
    async def _tick(self) -> None:
        now = dt.datetime.now(tz=TZ)
        if now.weekday() != POST_WEEKDAY or (now.hour, now.minute) < (POST_TIME.hour, POST_TIME.minute):
            return
        last = await self.last_posted()
        if last and last[0] == now.date().isoformat():
            return  # already posted today (also after a restart)
        try:
            await self.post_next(today=now.date().isoformat())
        except Exception:
            log.exception("WeeklyTip: post failed")

    @_tick.before_loop
    async def _before(self) -> None:
        await self.bot.wait_until_ready()

    async def post_next(self, *, today: str | None = None) -> int | None:
        index = await self.next_index()
        channel = self.bot.get_channel(self.channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(self.channel_id)
            except Exception as e:
                log.warning("WeeklyTip: announcements channel not found (%s)", e)
                return None
        await channel.send(tip_text(index), allowed_mentions=discord.AllowedMentions.none())
        today = today or dt.datetime.now(tz=TZ).date().isoformat()
        await self.repo.kv_set(self.guild_id, KV_LAST_INDEX, str(index))
        await self.repo.kv_set(self.guild_id, KV_LAST_POSTED, f"{today}|{int(time.time())}|{index}")
        log.info("WeeklyTip: posted tip %s (%s)", index + 1, TIPS[index][0])
        return index

    async def skip_next(self) -> int:
        """Move past the next tip without posting it. Returns the skipped index."""
        index = await self.next_index()
        await self.repo.kv_set(self.guild_id, KV_LAST_INDEX, str(index))
        log.info("WeeklyTip: skipped tip %s (%s)", index + 1, TIPS[index][0])
        return index
