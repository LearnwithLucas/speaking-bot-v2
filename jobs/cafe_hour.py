from __future__ import annotations

# jobs/cafe_hour.py
#
# Daily Café Hour (EN server only). One fixed time when members know others
# will be in voice, run entirely by the bot:
#
#   - keeps exactly one upcoming Discord event ("Café Hour: speak English together")
#   - 15 minutes before: one reminder in #looking-for-a-partner, pinging only the
#     Speaking Ping role (yesterday's reminder is deleted)
#   - at the start: starts the event and posts today's topic with 2 questions in the
#     voice channel's chat; after 30 minutes, one more question
#   - at the end: ends the event, stores unique speakers (3+ unmuted minutes),
#     voice minutes and the Interested count, then creates tomorrow's event
#
# The voice channel status is never touched: it shows levels (voice/table_tools.py).
# Every step is stored per session, so a restart never repeats a post.

import datetime as dt
import json
import logging
import random
import time
from typing import Any
from zoneinfo import ZoneInfo

import discord
from discord.ext import tasks

from commands.topics import EN_TOPICS
from config import (
    CAFE_HOUR_ANNOUNCE_CHANNEL_ID,
    CAFE_HOUR_DURATION_MIN,
    CAFE_HOUR_ENABLED,
    CAFE_HOUR_TIME,
    CAFE_HOUR_VOICE_CHANNEL_ID,
)
from jobs.partner_finder import I_WANT_TO_SPEAK_ROLE_ID

log = logging.getLogger("jobs.cafe_hour")

TZ = ZoneInfo("Europe/Amsterdam")
REMINDER_MINUTES = 15
FOLLOWUP_MINUTES = 30
MIN_SPEAKER_SECONDS = 3 * 60
TOPIC_NO_REPEAT_DAYS = 14

EVENT_NAME = "Café Hour: speak English together"
EVENT_DESCRIPTION = (
    "Join Open Conversation at this time. Other learners will be there. "
    "No teacher, no pressure. Just practise speaking. Press Interested to get a reminder."
)

# bot_kv keys (EN guild)
KV_EVENT = "cafe_hour_event"            # {"id": event_id, "start": epoch}
KV_REMINDER_MSG = "cafe_hour_reminder_msg"
KV_SKIP = "cafe_hour_skip_start"        # start epoch of the skipped session
KV_STATE = "cafe_hour_state:{start}"    # {"topic":..., "questions": [...], "reminded":, "posted":, "followup":, "ended":}


def parse_time(raw: str) -> dt.time | None:
    try:
        hour, minute = (int(x) for x in raw.split(":"))
        return dt.time(hour, minute)
    except Exception:
        return None


def session_start_for(now: dt.datetime, at: dt.time, duration_min: int) -> dt.datetime:
    """The session that hasn't ended yet: today's, or tomorrow's once today's is over. DST-safe."""
    local = now.astimezone(TZ)
    today = dt.datetime.combine(local.date(), at, tzinfo=TZ)
    if local < today + dt.timedelta(minutes=duration_min):
        return today
    return dt.datetime.combine(local.date() + dt.timedelta(days=1), at, tzinfo=TZ)


def pick_topic(recent: dict[str, int], rng: random.Random | None = None) -> str:
    """A topic not used in the last 14 days; with only 10 topics, the one used longest ago."""
    rng = rng or random.Random()
    keys = list(EN_TOPICS)
    unused = [k for k in keys if k not in recent]
    if unused:
        return rng.choice(unused)
    return min(keys, key=lambda k: recent[k])


class CafeHour:
    def __init__(self, *, bot: discord.Client, repo: Any, guild_id: int) -> None:
        self.bot = bot
        self.repo = repo
        self.guild_id = guild_id
        self.at = parse_time(CAFE_HOUR_TIME)
        self.duration = CAFE_HOUR_DURATION_MIN
        self.enabled = self._config_ok()
        self._warned: set[str] = set()
        if self.enabled:
            self._tick.start()
            log.info("CafeHour: on, daily at %s for %s min", CAFE_HOUR_TIME, self.duration)

    def _config_ok(self) -> bool:
        if not CAFE_HOUR_ENABLED:
            log.info("CafeHour: off (CAFE_HOUR_ENABLED is not true)")
            return False
        missing = [
            name
            for name, ok in (
                ("CAFE_HOUR_TIME", self.at is not None),
                ("CAFE_HOUR_DURATION_MIN", self.duration > 0),
                ("CAFE_HOUR_VOICE_CHANNEL_ID", bool(CAFE_HOUR_VOICE_CHANNEL_ID)),
                ("CAFE_HOUR_ANNOUNCE_CHANNEL_ID", bool(CAFE_HOUR_ANNOUNCE_CHANNEL_ID)),
            )
            if not ok
        ]
        if missing:
            log.warning("CafeHour: off, missing or invalid: %s", ", ".join(missing))
            return False
        return True

    def _warn_once(self, key: str, msg: str, *args: Any) -> None:
        if key in self._warned:
            return
        self._warned.add(key)
        log.warning(msg, *args)

    # -------------------------
    # Public helpers
    # -------------------------
    def next_start(self, now: dt.datetime | None = None) -> dt.datetime | None:
        if not self.enabled:
            return None
        return session_start_for(now or dt.datetime.now(tz=TZ), self.at, self.duration)

    async def is_skipped(self, start_epoch: int) -> bool:
        return await self.repo.kv_get(self.guild_id, KV_SKIP) == str(start_epoch)

    # -------------------------
    # State
    # -------------------------
    async def _state(self, start_epoch: int) -> dict[str, Any]:
        raw = await self.repo.kv_get(self.guild_id, KV_STATE.format(start=start_epoch))
        try:
            return json.loads(raw) if raw else {}
        except ValueError:
            return {}

    async def _save_state(self, start_epoch: int, state: dict[str, Any]) -> None:
        await self.repo.kv_set(self.guild_id, KV_STATE.format(start=start_epoch), json.dumps(state))

    async def _ensure_topic(self, start: dt.datetime, state: dict[str, Any]) -> dict[str, Any]:
        if state.get("topic"):
            return state
        since = int((start - dt.timedelta(days=TOPIC_NO_REPEAT_DAYS)).timestamp())
        recent = await self.repo.cafe_hour_recent_topics(self.guild_id, since)
        topic = pick_topic(recent)
        questions = random.sample(range(len(EN_TOPICS[topic]["questions"])), 3)
        state.update({"topic": topic, "questions": questions})
        start_epoch = int(start.timestamp())
        await self._save_state(start_epoch, state)
        await self.repo.cafe_hour_session_upsert(self.guild_id, start_epoch, start.date().isoformat(), topic=topic)
        return state

    # -------------------------
    # Loop
    # -------------------------
    @tasks.loop(seconds=30)
    async def _tick(self) -> None:
        try:
            await self.run_tick(dt.datetime.now(tz=TZ))
        except Exception:
            log.exception("CafeHour: tick failed")

    @_tick.before_loop
    async def _before(self) -> None:
        await self.bot.wait_until_ready()

    async def run_tick(self, now: dt.datetime) -> None:
        guild = self.bot.get_guild(self.guild_id)
        if guild is None:
            return

        # Finish a session that has ended (also after a restart).
        await self._finish_ended(guild, now)

        start = session_start_for(now, self.at, self.duration)
        start_epoch = int(start.timestamp())
        end = start + dt.timedelta(minutes=self.duration)

        if await self.is_skipped(start_epoch):
            await self._delete_event(guild, only_start=start_epoch)
            return

        await self._ensure_event(guild, start, end)

        state = await self._state(start_epoch)
        if start - dt.timedelta(minutes=REMINDER_MINUTES) <= now < start and not state.get("reminded"):
            state = await self._ensure_topic(start, state)
            await self._post_reminder(guild, state)
            state["reminded"] = True
            await self._save_state(start_epoch, state)

        if start <= now < end and not state.get("posted"):
            state = await self._ensure_topic(start, state)
            await self._start_event(guild)
            await self._post_topic(guild, state)
            state["posted"] = True
            await self._save_state(start_epoch, state)
            await self.repo.kv_set(self.guild_id, "cafe_hour_active_start", str(start_epoch))

        if start + dt.timedelta(minutes=FOLLOWUP_MINUTES) <= now < end and state.get("posted") and not state.get("followup"):
            await self._post_followup(guild, state)
            state["followup"] = True
            await self._save_state(start_epoch, state)

    # -------------------------
    # Event
    # -------------------------
    async def _stored_event(self) -> dict[str, int] | None:
        raw = await self.repo.kv_get(self.guild_id, KV_EVENT)
        try:
            data = json.loads(raw) if raw else None
            return {"id": int(data["id"]), "start": int(data["start"])} if data else None
        except (ValueError, KeyError, TypeError):
            return None

    async def _fetch_event(self, guild: discord.Guild, event_id: int, *, counts: bool = False) -> discord.ScheduledEvent | None:
        try:
            return await guild.fetch_scheduled_event(event_id, with_counts=counts)
        except discord.NotFound:
            return None
        except Exception as e:
            self._warn_once("fetch_event", "CafeHour: can't read events (%s)", e)
            return None

    async def _ensure_event(self, guild: discord.Guild, start: dt.datetime, end: dt.datetime) -> None:
        start_epoch = int(start.timestamp())
        stored = await self._stored_event()
        if stored and stored["start"] == start_epoch:
            event = await self._fetch_event(guild, stored["id"])
            if event is not None and event.status in (discord.EventStatus.scheduled, discord.EventStatus.active):
                return
        elif stored:
            # An event for another time (time changed in config): remove it if it hasn't run.
            old = await self._fetch_event(guild, stored["id"])
            if old is not None and old.status == discord.EventStatus.scheduled:
                try:
                    await old.delete()
                except Exception as e:
                    self._warn_once("delete_event", "CafeHour: can't delete old event (%s)", e)

        if start <= dt.datetime.now(tz=TZ):
            return  # Discord can't schedule an event in the past; tomorrow's gets created after this one.

        channel = guild.get_channel(CAFE_HOUR_VOICE_CHANNEL_ID)
        if not isinstance(channel, (discord.VoiceChannel, discord.StageChannel)):
            self._warn_once("voice_channel", "CafeHour: voice channel %s not found", CAFE_HOUR_VOICE_CHANNEL_ID)
            return
        try:
            event = await guild.create_scheduled_event(
                name=EVENT_NAME,
                description=EVENT_DESCRIPTION,
                start_time=start,
                end_time=end,
                channel=channel,
                entity_type=discord.EntityType.voice,
                privacy_level=discord.PrivacyLevel.guild_only,
            )
        except Exception as e:
            self._warn_once("create_event", "CafeHour: can't create the event (Manage Events?) (%s)", e)
            return
        await self.repo.kv_set(self.guild_id, KV_EVENT, json.dumps({"id": event.id, "start": start_epoch}))
        log.info("CafeHour: event created id=%s start=%s", event.id, start.isoformat())

    async def _start_event(self, guild: discord.Guild) -> None:
        stored = await self._stored_event()
        if not stored:
            return
        event = await self._fetch_event(guild, stored["id"])
        if event is not None and event.status == discord.EventStatus.scheduled:
            try:
                await event.start()
            except Exception as e:
                self._warn_once("start_event", "CafeHour: can't start the event (%s)", e)

    async def _delete_event(self, guild: discord.Guild, *, only_start: int) -> None:
        stored = await self._stored_event()
        if not stored or stored["start"] != only_start:
            return
        event = await self._fetch_event(guild, stored["id"])
        if event is not None:
            try:
                await event.delete()
                log.info("CafeHour: event deleted id=%s (skipped)", stored["id"])
            except Exception as e:
                self._warn_once("delete_event", "CafeHour: can't delete event (%s)", e)
                return
        await self.repo.kv_set(self.guild_id, KV_EVENT, "")

    async def _finish_ended(self, guild: discord.Guild, now: dt.datetime) -> None:
        raw = await self.repo.kv_get(self.guild_id, "cafe_hour_active_start")
        if not raw:
            return
        start_epoch = int(raw)
        end_epoch = start_epoch + self.duration * 60
        if now.timestamp() < end_epoch:
            return

        interested = None
        stored = await self._stored_event()
        if stored and stored["start"] == start_epoch:
            event = await self._fetch_event(guild, stored["id"], counts=True)
            if event is not None:
                interested = event.user_count
                if event.status == discord.EventStatus.active:
                    try:
                        await event.end()
                    except Exception as e:
                        self._warn_once("end_event", "CafeHour: can't end the event (%s)", e)

        speakers, seconds = await self.repo.voice_speakers_in_window(
            self.guild_id, CAFE_HOUR_VOICE_CHANNEL_ID, start_epoch, end_epoch, MIN_SPEAKER_SECONDS
        )
        day = dt.datetime.fromtimestamp(start_epoch, tz=TZ).date().isoformat()
        await self.repo.cafe_hour_session_upsert(
            self.guild_id,
            start_epoch,
            day,
            unique_speakers=speakers,
            voice_minutes=seconds // 60,
            interested=interested,
        )
        await self.repo.kv_set(self.guild_id, "cafe_hour_active_start", "")
        log.info("CafeHour: session %s ended speakers=%s minutes=%s interested=%s", day, speakers, seconds // 60, interested)

    # -------------------------
    # Posts
    # -------------------------
    def reminder_text(self, state: dict[str, Any]) -> str:
        label = EN_TOPICS[state["topic"]]["label"]
        return (
            f"<@&{I_WANT_TO_SPEAK_ROLE_ID}> Café Hour starts in 15 minutes in <#{CAFE_HOUR_VOICE_CHANNEL_ID}>.\n"
            f"Today's topic: **{label}**. Come for 10 minutes or stay the whole hour."
        )

    def topic_text(self, state: dict[str, Any]) -> str:
        topic = EN_TOPICS[state["topic"]]
        q = [topic["questions"][i] for i in state["questions"][:2]]
        lines = [f"☕ **Café Hour has started.** Today's topic: **{topic['label']}**", ""]
        for n, (question, hint) in enumerate(q, start=1):
            lines.append(f"{n}. {question}")
            lines.append(f"   {hint}")
        lines += ["", "Pick one question and start. One sentence is enough."]
        return "\n".join(lines)

    def followup_text(self, state: dict[str, Any]) -> str:
        question, hint = EN_TOPICS[state["topic"]]["questions"][state["questions"][2]]
        return f"☕ **Halfway there.** One more question:\n{question}\n{hint}"

    async def _post_reminder(self, guild: discord.Guild, state: dict[str, Any]) -> None:
        channel = guild.get_channel(CAFE_HOUR_ANNOUNCE_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            self._warn_once("announce_channel", "CafeHour: announce channel %s not found", CAFE_HOUR_ANNOUNCE_CHANNEL_ID)
            return
        old_id = await self.repo.kv_get(self.guild_id, KV_REMINDER_MSG)
        if old_id:
            try:
                await channel.get_partial_message(int(old_id)).delete()
            except Exception:
                pass
        role = guild.get_role(I_WANT_TO_SPEAK_ROLE_ID)
        try:
            message = await channel.send(
                self.reminder_text(state),
                allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=[role] if role else False),
            )
            await self.repo.kv_set(self.guild_id, KV_REMINDER_MSG, str(message.id))
            log.info("CafeHour: reminder posted topic=%s", state["topic"])
        except Exception as e:
            self._warn_once("reminder", "CafeHour: can't post the reminder (%s)", e)

    async def _voice_chat(self, guild: discord.Guild) -> discord.VoiceChannel | None:
        channel = guild.get_channel(CAFE_HOUR_VOICE_CHANNEL_ID)
        if isinstance(channel, discord.VoiceChannel):
            return channel
        self._warn_once("voice_channel", "CafeHour: voice channel %s not found", CAFE_HOUR_VOICE_CHANNEL_ID)
        return None

    async def _post_topic(self, guild: discord.Guild, state: dict[str, Any]) -> None:
        channel = await self._voice_chat(guild)
        if channel is None:
            return
        try:
            await channel.send(self.topic_text(state), allowed_mentions=discord.AllowedMentions.none())
            log.info("CafeHour: topic posted topic=%s", state["topic"])
        except Exception as e:
            self._warn_once("topic", "CafeHour: can't post in the voice chat (%s)", e)

    async def _post_followup(self, guild: discord.Guild, state: dict[str, Any]) -> None:
        channel = await self._voice_chat(guild)
        if channel is None:
            return
        try:
            await channel.send(self.followup_text(state), allowed_mentions=discord.AllowedMentions.none())
        except Exception as e:
            self._warn_once("topic", "CafeHour: can't post in the voice chat (%s)", e)

    # -------------------------
    # Admin
    # -------------------------
    async def skip_next(self) -> dt.datetime | None:
        start = self.next_start()
        if start is None:
            return None
        start_epoch = int(start.timestamp())
        await self.repo.kv_set(self.guild_id, KV_SKIP, str(start_epoch))
        await self.repo.cafe_hour_session_upsert(self.guild_id, start_epoch, start.date().isoformat(), skipped=1)
        guild = self.bot.get_guild(self.guild_id)
        if guild is not None:
            await self._delete_event(guild, only_start=start_epoch)
        log.info("CafeHour: skipping session %s", start.isoformat())
        return start

    async def preview(self) -> tuple[str, str, str]:
        """Reminder, topic and follow-up text for a test run. Stores nothing."""
        state = {"topic": pick_topic({}), "questions": []}
        state["questions"] = random.sample(range(len(EN_TOPICS[state["topic"]]["questions"])), 3)
        return self.reminder_text(state), self.topic_text(state), self.followup_text(state)

    async def status(self) -> dict[str, Any]:
        start = self.next_start()
        state = await self._state(int(start.timestamp())) if start else {}
        sessions = await self.repo.cafe_hour_sessions_since(self.guild_id, int(time.time()) - 30 * 86400)
        held = [s for s in sessions if not s["skipped"] and s["unique_speakers"] is not None][:7]
        return {
            "next": start,
            "skipped": bool(start and await self.is_skipped(int(start.timestamp()))),
            "topic": EN_TOPICS[state["topic"]]["label"] if state.get("topic") else None,
            "recent": held,
        }


def summarize_sessions(sessions: list[dict[str, Any]]) -> str:
    """For /adminhealth: last 14 days."""
    held = [s for s in sessions if not s["skipped"] and s["unique_speakers"] is not None]
    if not held:
        return "No sessions held yet."
    avg = sum(s["unique_speakers"] for s in held) / len(held)
    best = max(held, key=lambda s: s["unique_speakers"])
    worst = min(held, key=lambda s: s["unique_speakers"])
    interested = [s["interested"] for s in held if s["interested"] is not None]
    avg_int = f"{sum(interested) / len(interested):.1f}" if interested else "n/a"
    return (
        f"Sessions held: **{len(held)}**\n"
        f"Average unique speakers: **{avg:.1f}** (goal: 3+)\n"
        f"Best day: **{best['day']}** ({best['unique_speakers']})\n"
        f"Worst day: **{worst['day']}** ({worst['unique_speakers']})\n"
        f"Average Interested: **{avg_int}**"
    )
