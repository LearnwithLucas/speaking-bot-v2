import aiosqlite
import json
import time
import sqlite3
from typing import Optional, List, Tuple, Dict, Any
from .schema import SCHEMA_SQL

class Repo:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        self._conn = await aiosqlite.connect(self.db_path)
        await self._conn.executescript(SCHEMA_SQL)
        await self._conn.commit()

        # Lightweight, additive migrations for existing DB files
        await self._migrate()
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if not self._conn:
            raise RuntimeError("Repo not connected")
        return self._conn

    # -------------------------
    # Migrations (safe + additive)
    # -------------------------
    async def _table_exists(self, table: str) -> bool:
        cur = await self.conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
            (table,),
        )
        row = await cur.fetchone()
        return bool(row)

    async def _table_columns(self, table: str) -> set[str]:
        cur = await self.conn.execute(f"PRAGMA table_info({table})")
        rows = await cur.fetchall()
        # rows: (cid, name, type, notnull, dflt_value, pk)
        return {str(r[1]) for r in rows}

    async def _migrate(self) -> None:
        # user_state.last_inactivity_nudge_at was added later; old DBs may not have it.
        if await self._table_exists("user_state"):
            cols = await self._table_columns("user_state")

            if "last_inactivity_nudge_at" not in cols:
                await self.conn.execute(
                    "ALTER TABLE user_state ADD COLUMN last_inactivity_nudge_at INTEGER"
                )

            # Optional: if an older column existed, copy its data forward once.
            cols = await self._table_columns("user_state")
            if "last_inactivity_dm_at" in cols and "last_inactivity_nudge_at" in cols:
                await self.conn.execute(
                    """
                    UPDATE user_state
                    SET last_inactivity_nudge_at = last_inactivity_dm_at
                    WHERE last_inactivity_nudge_at IS NULL AND last_inactivity_dm_at IS NOT NULL
                    """
                )

    # -------------------------
    # Voice sessions
    # -------------------------
    async def start_session(self, guild_id: int, user_id: int, channel_id: int, started_at: int) -> None:
        # A session still open here means we missed the leave event. We don't
        # know when it really ended, so it counts as zero instead of the gap.
        await self.conn.execute(
            """
            UPDATE voice_sessions
            SET ended_at = started_at
            WHERE guild_id = ? AND user_id = ? AND ended_at IS NULL
            """,
            (guild_id, user_id),
        )
        await self.conn.execute(
            """
            INSERT INTO voice_sessions (guild_id, user_id, channel_id, started_at, ended_at)
            VALUES (?, ?, ?, ?, NULL)
            """,
            (guild_id, user_id, channel_id, started_at),
        )
        await self.conn.commit()

    async def end_open_session(self, guild_id: int, user_id: int, ended_at: Optional[int] = None) -> int:
        if ended_at is None:
            ended_at = int(time.time())
        cur = await self.conn.execute(
            """
            UPDATE voice_sessions
            SET ended_at = ?
            WHERE guild_id = ? AND user_id = ? AND ended_at IS NULL
            """,
            (ended_at, guild_id, user_id),
        )
        await self.conn.commit()
        return cur.rowcount

    async def close_all_open_sessions(self, guild_id: int, at: int) -> int:
        """Close every open session in a guild at `at` (never before its own start)."""
        cur = await self.conn.execute(
            """
            UPDATE voice_sessions
            SET ended_at = MAX(started_at, ?)
            WHERE guild_id = ? AND ended_at IS NULL
            """,
            (at, guild_id),
        )
        await self.conn.commit()
        return int(cur.rowcount or 0)

    async def compute_and_cache_total_seconds(self, guild_id: int, user_id: int) -> int:
        cur = await self.conn.execute(
            """
            SELECT COALESCE(SUM(ended_at - started_at), 0)
            FROM voice_sessions
            WHERE guild_id = ? AND user_id = ? AND ended_at IS NOT NULL
            """,
            (guild_id, user_id),
        )
        (total,) = await cur.fetchone()
        total = int(total or 0)

        await self.conn.execute(
            """
            INSERT INTO speaking_cache (guild_id, user_id, total_seconds)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id, user_id)
            DO UPDATE SET total_seconds=excluded.total_seconds
            """,
            (guild_id, user_id, total),
        )
        await self.conn.commit()
        return total

    async def leaderboard_seconds(self, guild_id: int, since_epoch: Optional[int], limit: int = 10) -> List[Tuple[int, int]]:
        # (Legacy helper, kept for now; not exposed publicly.)
        if since_epoch is None:
            cur = await self.conn.execute(
                """
                SELECT user_id, COALESCE(SUM(ended_at - started_at), 0) AS seconds
                FROM voice_sessions
                WHERE guild_id = ? AND ended_at IS NOT NULL
                GROUP BY user_id
                ORDER BY seconds DESC
                LIMIT ?
                """,
                (guild_id, limit),
            )
        else:
            cur = await self.conn.execute(
                """
                SELECT user_id, COALESCE(SUM(ended_at - started_at), 0) AS seconds
                FROM voice_sessions
                WHERE guild_id = ? AND ended_at IS NOT NULL AND ended_at >= ?
                GROUP BY user_id
                ORDER BY seconds DESC
                LIMIT ?
                """,
                (guild_id, since_epoch, limit),
            )
        rows = await cur.fetchall()
        return [(int(uid), int(sec or 0)) for (uid, sec) in rows]

    async def user_voice_seconds_since(self, guild_id: int, user_id: int, since_epoch: int) -> int:
        now_epoch = int(time.time())
        cur = await self.conn.execute(
            """
            SELECT COALESCE(SUM(
                CASE
                    WHEN COALESCE(ended_at, ?) <= ? THEN 0
                    ELSE COALESCE(ended_at, ?) -
                        CASE WHEN started_at < ? THEN ? ELSE started_at END
                END
            ), 0)
            FROM voice_sessions
            WHERE guild_id = ?
              AND user_id = ?
              AND started_at <= ?
              AND COALESCE(ended_at, ?) >= ?
            """,
            (
                now_epoch,
                since_epoch,
                now_epoch,
                since_epoch,
                since_epoch,
                guild_id,
                user_id,
                now_epoch,
                now_epoch,
                since_epoch,
            ),
        )
        (total,) = await cur.fetchone()
        return max(0, int(total or 0))

    async def move_sessions_to_guild(self, from_guild_id: int, to_guild_id: int, channel_ids: list[int]) -> int:
        """Move voice sessions recorded under the wrong server (by channel) to the right one."""
        if not channel_ids:
            return 0
        placeholders = ",".join("?" for _ in channel_ids)
        cur = await self.conn.execute(
            f"""
            UPDATE voice_sessions
            SET guild_id = ?
            WHERE guild_id = ? AND channel_id IN ({placeholders})
            """,
            (to_guild_id, from_guild_id, *channel_ids),
        )
        await self.conn.execute("DELETE FROM speaking_cache WHERE guild_id IN (?, ?)", (from_guild_id, to_guild_id))
        await self.conn.commit()
        return int(cur.rowcount or 0)

    async def winback_candidates(self, guild_id: int, now_epoch: int, min_days: int, max_days: int) -> list[tuple[int, int]]:
        """
        Members whose last voice time ended between max_days and min_days ago,
        and who got no win-back DM since that last voice time.
        Returns [(user_id, last_voice_at)]. Members in voice right now are excluded.
        """
        cur = await self.conn.execute(
            """
            SELECT v.user_id, v.last_at
            FROM (
                SELECT user_id, MAX(COALESCE(ended_at, ?)) AS last_at
                FROM voice_sessions
                WHERE guild_id = ?
                GROUP BY user_id
            ) v
            LEFT JOIN user_state u ON u.guild_id = ? AND u.user_id = v.user_id
            WHERE v.last_at <= ? AND v.last_at > ?
              AND (u.last_inactivity_nudge_at IS NULL OR u.last_inactivity_nudge_at < v.last_at)
            ORDER BY v.last_at ASC
            """,
            (
                now_epoch,
                guild_id,
                guild_id,
                now_epoch - min_days * 86400,
                now_epoch - max_days * 86400,
            ),
        )
        return [(int(uid), int(at)) for uid, at in await cur.fetchall()]

    async def member_level_get(self, guild_id: int, user_id: int) -> str | None:
        cur = await self.conn.execute(
            "SELECT level FROM member_levels WHERE guild_id=? AND user_id=?",
            (guild_id, user_id),
        )
        row = await cur.fetchone()
        return str(row[0]) if row else None

    async def member_level_set(self, guild_id: int, user_id: int, level: str, at: int) -> None:
        await self.conn.execute(
            """
            INSERT INTO member_levels (guild_id, user_id, level, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(guild_id, user_id) DO UPDATE SET level=excluded.level, updated_at=excluded.updated_at
            """,
            (guild_id, user_id, level, at),
        )
        await self.conn.commit()

    # -------------------------
    # Server Tag
    # -------------------------
    async def tag_get(self, guild_id: int, user_id: int) -> dict[str, Any] | None:
        cur = await self.conn.execute(
            "SELECT wears_tag, first_seen_wearing, last_checked, thanked_at, last_asked_at "
            "FROM member_tags WHERE guild_id=? AND user_id=?",
            (guild_id, user_id),
        )
        row = await cur.fetchone()
        if not row:
            return None
        keys = ("wears_tag", "first_seen_wearing", "last_checked", "thanked_at", "last_asked_at")
        return dict(zip(keys, row))

    async def tag_record(self, guild_id: int, user_id: int, wears: bool, at: int) -> bool:
        """Store the current state. True if this is the first time ever we see them wearing it."""
        before = await self.tag_get(guild_id, user_id)
        first_time = wears and (before is None or before["first_seen_wearing"] is None)
        await self.conn.execute(
            """
            INSERT INTO member_tags (guild_id, user_id, wears_tag, first_seen_wearing, last_checked)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(guild_id, user_id) DO UPDATE SET
                wears_tag=excluded.wears_tag,
                first_seen_wearing=COALESCE(member_tags.first_seen_wearing, excluded.first_seen_wearing),
                last_checked=excluded.last_checked
            """,
            (guild_id, user_id, 1 if wears else 0, at if wears else None, at),
        )
        await self.conn.commit()
        return first_time

    async def tag_mark_thanked(self, guild_id: int, user_id: int, at: int) -> bool:
        """Claim the once-ever thank-you. False if already thanked."""
        cur = await self.conn.execute(
            "UPDATE member_tags SET thanked_at=? WHERE guild_id=? AND user_id=? AND thanked_at IS NULL",
            (at, guild_id, user_id),
        )
        await self.conn.commit()
        return (cur.rowcount or 0) > 0

    async def tag_mark_asked(self, guild_id: int, user_id: int, at: int) -> None:
        await self.conn.execute(
            """
            INSERT INTO member_tags (guild_id, user_id, wears_tag, last_checked, last_asked_at)
            VALUES (?, ?, 0, ?, ?)
            ON CONFLICT(guild_id, user_id) DO UPDATE SET last_asked_at=excluded.last_asked_at
            """,
            (guild_id, user_id, at, at),
        )
        await self.conn.commit()

    async def tag_stats(self, guild_id: int, week_ago: int, speaking_since: int) -> dict[str, int]:
        now = int(time.time())
        cur = await self.conn.execute(
            "SELECT SUM(wears_tag), SUM(CASE WHEN first_seen_wearing >= ? THEN 1 ELSE 0 END) FROM member_tags WHERE guild_id=?",
            (week_ago, guild_id),
        )
        wearing, new_week = await cur.fetchone()
        cur = await self.conn.execute(
            """
            SELECT COUNT(*), SUM(COALESCE(t.wears_tag, 0))
            FROM (
                SELECT user_id,
                       SUM(COALESCE(ended_at, ?) - MAX(started_at, ?)) AS secs
                FROM voice_sessions
                WHERE guild_id = ? AND COALESCE(ended_at, ?) > ?
                GROUP BY user_id
            ) v
            LEFT JOIN member_tags t ON t.guild_id = ? AND t.user_id = v.user_id
            WHERE v.secs >= 3600
            """,
            (now, speaking_since, guild_id, now, speaking_since, guild_id),
        )
        speakers, speakers_wearing = await cur.fetchone()
        return {
            "wearing": int(wearing or 0),
            "new_week": int(new_week or 0),
            "speakers_1h": int(speakers or 0),
            "speakers_1h_wearing": int(speakers_wearing or 0),
        }

    # -------------------------
    # Member profile (/profile)
    # -------------------------
    async def profile_people_met(self, guild_id: int, user_id: int) -> int:
        cur = await self.conn.execute(
            """
            SELECT COUNT(DISTINCT CASE WHEN user_a_id = ? THEN user_b_id ELSE user_a_id END)
            FROM voice_met
            WHERE guild_id = ? AND (user_a_id = ? OR user_b_id = ?)
            """,
            (user_id, guild_id, user_id, user_id),
        )
        return int((await cur.fetchone())[0] or 0)

    async def profile_achievements(self, guild_id: int, user_id: int) -> list[tuple[str, int]]:
        cur = await self.conn.execute(
            "SELECT achievement_id, earned_at FROM achievements WHERE guild_id=? AND user_id=? ORDER BY earned_at",
            (guild_id, user_id),
        )
        return [(str(a), int(t)) for a, t in await cur.fetchall()]

    async def profile_session_starts(self, guild_id: int, user_id: int) -> list[int]:
        cur = await self.conn.execute(
            "SELECT started_at FROM voice_sessions WHERE guild_id=? AND user_id=?",
            (guild_id, user_id),
        )
        return [int(r[0]) for r in await cur.fetchall()]

    async def profile_cafe_hours_joined(self, guild_id: int, user_id: int, channel_id: int, duration_seconds: int, min_seconds: int) -> int:
        """Held Café Hour sessions where this member had min_seconds+ of voice time in the channel."""
        now = int(time.time())
        cur = await self.conn.execute(
            """
            SELECT COUNT(*) FROM (
                SELECT c.start_at,
                       SUM(MIN(COALESCE(v.ended_at, ?), c.start_at + ?) - MAX(v.started_at, c.start_at)) AS secs
                FROM cafe_hour_sessions c
                JOIN voice_sessions v
                  ON v.guild_id = c.guild_id
                 AND v.user_id = ?
                 AND v.channel_id = ?
                 AND v.started_at < c.start_at + ?
                 AND COALESCE(v.ended_at, ?) > c.start_at
                WHERE c.guild_id = ? AND c.skipped = 0
                GROUP BY c.start_at
            ) WHERE secs >= ?
            """,
            (now, duration_seconds, user_id, channel_id, duration_seconds, now, guild_id, min_seconds),
        )
        return int((await cur.fetchone())[0] or 0)

    # -------------------------
    # Café Hour
    # -------------------------
    async def cafe_hour_session_upsert(self, guild_id: int, start_at: int, day: str, **fields: Any) -> None:
        await self.conn.execute(
            "INSERT OR IGNORE INTO cafe_hour_sessions (guild_id, start_at, day) VALUES (?, ?, ?)",
            (guild_id, start_at, day),
        )
        allowed = {"topic", "skipped", "unique_speakers", "voice_minutes", "interested"}
        for key, value in fields.items():
            if key in allowed:
                await self.conn.execute(
                    f"UPDATE cafe_hour_sessions SET {key}=? WHERE guild_id=? AND start_at=?",
                    (value, guild_id, start_at),
                )
        await self.conn.commit()

    async def cafe_hour_recent_topics(self, guild_id: int, since_epoch: int) -> dict[str, int]:
        """topic -> last start_at it was used."""
        cur = await self.conn.execute(
            "SELECT topic, MAX(start_at) FROM cafe_hour_sessions "
            "WHERE guild_id=? AND start_at>=? AND topic IS NOT NULL AND skipped=0 GROUP BY topic",
            (guild_id, since_epoch),
        )
        return {str(t): int(at) for t, at in await cur.fetchall()}

    async def cafe_hour_sessions_since(self, guild_id: int, since_epoch: int) -> list[dict[str, Any]]:
        cur = await self.conn.execute(
            "SELECT start_at, day, topic, skipped, unique_speakers, voice_minutes, interested "
            "FROM cafe_hour_sessions WHERE guild_id=? AND start_at>=? ORDER BY start_at DESC",
            (guild_id, since_epoch),
        )
        keys = ("start_at", "day", "topic", "skipped", "unique_speakers", "voice_minutes", "interested")
        return [dict(zip(keys, row)) for row in await cur.fetchall()]

    async def voice_speakers_in_window(
        self, guild_id: int, channel_id: int, start_at: int, end_at: int, min_seconds: int
    ) -> tuple[int, int]:
        """
        (members with at least min_seconds of counted voice time in this
        channel inside the window, total counted seconds in the window).
        Only unmuted time is ever stored, so this is speaking time.
        """
        now = int(time.time())
        cur = await self.conn.execute(
            """
            SELECT user_id,
                   SUM(MIN(COALESCE(ended_at, ?), ?) - MAX(started_at, ?)) AS secs
            FROM voice_sessions
            WHERE guild_id=? AND channel_id=? AND started_at < ? AND COALESCE(ended_at, ?) > ?
            GROUP BY user_id
            """,
            (now, end_at, start_at, guild_id, channel_id, end_at, now, start_at),
        )
        rows = await cur.fetchall()
        speakers = sum(1 for _uid, secs in rows if (secs or 0) >= min_seconds)
        total = sum(max(0, secs or 0) for _uid, secs in rows)
        return speakers, int(total)

    # -------------------------
    # Milestone shout-outs
    # -------------------------
    async def milestone_announcement_claim(
        self, guild_id: int, user_id: int, milestone: str, at: int, *, posted: bool = True
    ) -> bool:
        """Mark a milestone as announced. False if it already was (so never post twice)."""
        cur = await self.conn.execute(
            "INSERT OR IGNORE INTO milestone_announcements (guild_id, user_id, milestone, announced_at, posted) "
            "VALUES (?, ?, ?, ?, ?)",
            (guild_id, user_id, milestone, at, 1 if posted else 0),
        )
        await self.conn.commit()
        return (cur.rowcount or 0) > 0

    async def milestone_shoutouts_enabled(self, guild_id: int, user_id: int) -> bool:
        cur = await self.conn.execute(
            "SELECT milestone_shoutouts_enabled FROM member_settings WHERE guild_id=? AND user_id=?",
            (guild_id, user_id),
        )
        row = await cur.fetchone()
        return True if row is None else bool(row[0])

    async def milestone_shoutouts_set(self, guild_id: int, user_id: int, enabled: bool, at: int) -> None:
        await self.conn.execute(
            """
            INSERT INTO member_settings (guild_id, user_id, milestone_shoutouts_enabled, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(guild_id, user_id) DO UPDATE SET
                milestone_shoutouts_enabled=excluded.milestone_shoutouts_enabled,
                updated_at=excluded.updated_at
            """,
            (guild_id, user_id, 1 if enabled else 0, at),
        )
        await self.conn.commit()

    async def milestone_shoutout_counts(self, guild_id: int, since_epoch: int) -> dict[str, int]:
        cur = await self.conn.execute(
            "SELECT COUNT(*) FROM milestone_announcements WHERE guild_id=? AND posted=1 AND announced_at >= ?",
            (guild_id, since_epoch),
        )
        posted = (await cur.fetchone())[0]
        cur = await self.conn.execute(
            "SELECT COUNT(*) FROM member_settings WHERE guild_id=? AND milestone_shoutouts_enabled=0",
            (guild_id,),
        )
        opted_out = (await cur.fetchone())[0]
        return {"posted": int(posted or 0), "opted_out": int(opted_out or 0)}

    # -------------------------
    # Conversation Host invites
    # -------------------------
    async def host_invite_create(self, guild_id: int, user_id: int, at: int) -> bool:
        """Insert the invite. False if this member was already invited."""
        cur = await self.conn.execute(
            "INSERT OR IGNORE INTO host_invites (guild_id, user_id, invited_at) VALUES (?, ?, ?)",
            (guild_id, user_id, at),
        )
        await self.conn.commit()
        return (cur.rowcount or 0) > 0

    async def host_invite_get(self, guild_id: int, user_id: int) -> dict[str, Any] | None:
        cur = await self.conn.execute(
            "SELECT invited_at, answer, answered_at, decision, decided_at, decided_by "
            "FROM host_invites WHERE guild_id=? AND user_id=?",
            (guild_id, user_id),
        )
        row = await cur.fetchone()
        if not row:
            return None
        keys = ("invited_at", "answer", "answered_at", "decision", "decided_at", "decided_by")
        return dict(zip(keys, row))

    async def host_invite_answer(self, guild_id: int, user_id: int, answer: str, at: int) -> bool:
        """Store the member's answer once. False if there's no open invite."""
        cur = await self.conn.execute(
            "UPDATE host_invites SET answer=?, answered_at=? WHERE guild_id=? AND user_id=? AND answer IS NULL",
            (answer, at, guild_id, user_id),
        )
        await self.conn.commit()
        return (cur.rowcount or 0) > 0

    async def host_invite_decide(self, guild_id: int, user_id: int, decision: str, by: int, at: int) -> bool:
        """Store Lucas's decision once. False if already decided or not a yes."""
        cur = await self.conn.execute(
            "UPDATE host_invites SET decision=?, decided_at=?, decided_by=? "
            "WHERE guild_id=? AND user_id=? AND answer='yes' AND decision IS NULL",
            (decision, at, by, guild_id, user_id),
        )
        await self.conn.commit()
        return (cur.rowcount or 0) > 0

    async def host_invite_counts(self, guild_id: int) -> dict[str, int]:
        cur = await self.conn.execute(
            """
            SELECT
                COUNT(*),
                SUM(CASE WHEN answer='yes' THEN 1 ELSE 0 END),
                SUM(CASE WHEN decision='approved' THEN 1 ELSE 0 END)
            FROM host_invites WHERE guild_id=?
            """,
            (guild_id,),
        )
        sent, yes, approved = await cur.fetchone()
        return {"sent": int(sent or 0), "yes": int(yes or 0), "approved": int(approved or 0)}

    async def user_weeks_active(self, guild_id: int, user_id: int) -> int:
        """Number of distinct weeks with any voice time."""
        cur = await self.conn.execute(
            "SELECT COUNT(DISTINCT strftime('%Y-%W', started_at, 'unixepoch')) "
            "FROM voice_sessions WHERE guild_id=? AND user_id=?",
            (guild_id, user_id),
        )
        row = await cur.fetchone()
        return int(row[0] or 0)

    async def users_with_voice_since(self, guild_id: int, since_epoch: int) -> list[int]:
        cur = await self.conn.execute(
            "SELECT DISTINCT user_id FROM voice_sessions WHERE guild_id=? AND COALESCE(ended_at, started_at) >= ?",
            (guild_id, since_epoch),
        )
        return [int(r[0]) for r in await cur.fetchall()]

    # -------------------------
    # Member joins (activation stat)
    # -------------------------
    async def member_join_record(self, guild_id: int, user_id: int, joined_at: int) -> None:
        await self.conn.execute(
            """
            INSERT INTO member_joins (guild_id, user_id, joined_at)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id, user_id) DO UPDATE SET joined_at=excluded.joined_at
            """,
            (guild_id, user_id, joined_at),
        )
        await self.conn.commit()

    async def member_joins_backfill(self, guild_id: int, rows: list[tuple[int, int]]) -> None:
        """Insert (user_id, joined_at) for current members we have no record of yet."""
        await self.conn.executemany(
            "INSERT OR IGNORE INTO member_joins (guild_id, user_id, joined_at) VALUES (?, ?, ?)",
            [(guild_id, uid, at) for uid, at in rows],
        )
        await self.conn.commit()

    async def new_member_voice_rate(self, guild_id: int, now_epoch: int, cohort_days: int = 30) -> tuple[int, int]:
        """
        Of members who joined between (now - 7d - cohort_days) and (now - 7d),
        how many had counted (unmuted) voice time within 7 days of joining.
        Returns (in_voice, cohort_size). Only full 7-day windows are counted.
        """
        week = 7 * 86400
        cohort_end = now_epoch - week
        cohort_start = cohort_end - cohort_days * 86400
        cur = await self.conn.execute(
            """
            SELECT
                COUNT(*),
                SUM(CASE WHEN EXISTS (
                    SELECT 1 FROM voice_sessions s
                    WHERE s.guild_id = j.guild_id
                      AND s.user_id = j.user_id
                      AND s.started_at >= j.joined_at
                      AND s.started_at < j.joined_at + ?
                ) THEN 1 ELSE 0 END)
            FROM member_joins j
            WHERE j.guild_id = ? AND j.joined_at >= ? AND j.joined_at < ?
            """,
            (week, guild_id, cohort_start, cohort_end),
        )
        cohort, in_voice = await cur.fetchone()
        return int(in_voice or 0), int(cohort or 0)

    async def command_usage_record(self, guild_id: int, user_id: int, command_name: str, used_at: int | None = None) -> None:
        if used_at is None:
            used_at = int(time.time())
        await self.conn.execute(
            """
            INSERT INTO command_usage (guild_id, user_id, command_name, used_at)
            VALUES (?, ?, ?, ?)
            """,
            (guild_id, user_id, command_name, used_at),
        )
        await self.conn.commit()

    async def community_health_summary(self, guild_id: int, since_epoch: int) -> dict[str, Any]:
        now_epoch = int(time.time())

        cur = await self.conn.execute(
            """
            SELECT
                COUNT(*) AS sessions,
                COUNT(DISTINCT user_id) AS active_users,
                COALESCE(SUM(
                    CASE
                        WHEN COALESCE(ended_at, ?) <= ? THEN 0
                        ELSE COALESCE(ended_at, ?) -
                            CASE WHEN started_at < ? THEN ? ELSE started_at END
                    END
                ), 0) AS seconds
            FROM voice_sessions
            WHERE guild_id = ?
              AND started_at <= ?
              AND COALESCE(ended_at, ?) >= ?
            """,
            (
                now_epoch,
                since_epoch,
                now_epoch,
                since_epoch,
                since_epoch,
                guild_id,
                now_epoch,
                now_epoch,
                since_epoch,
            ),
        )
        sessions, active_users, seconds = await cur.fetchone()

        cur = await self.conn.execute(
            "SELECT COUNT(DISTINCT user_id) FROM voice_sessions WHERE guild_id=? AND ended_at IS NULL",
            (guild_id,),
        )
        (active_now,) = await cur.fetchone()

        cur = await self.conn.execute(
            "SELECT COUNT(*) FROM user_state WHERE guild_id=? AND last_weekly_dm_at >= ?",
            (guild_id, since_epoch),
        )
        (weekly_recaps_sent,) = await cur.fetchone()

        cur = await self.conn.execute(
            "SELECT COUNT(*) FROM user_state WHERE guild_id=? AND last_inactivity_nudge_at >= ?",
            (guild_id, since_epoch),
        )
        (inactivity_nudges_sent,) = await cur.fetchone()

        cur = await self.conn.execute(
            "SELECT COUNT(*) FROM achievements WHERE guild_id=? AND earned_at >= ?",
            (guild_id, since_epoch),
        )
        (achievements_awarded,) = await cur.fetchone()

        cur = await self.conn.execute(
            "SELECT COUNT(*) FROM voice_met WHERE guild_id=? AND first_met_at >= ?",
            (guild_id, since_epoch),
        )
        (new_voice_pairs,) = await cur.fetchone()

        cur = await self.conn.execute(
            "SELECT COUNT(DISTINCT user_id) FROM partner_slots WHERE guild_id=? AND updated_at >= ?",
            (guild_id, since_epoch),
        )
        (partner_profiles_updated,) = await cur.fetchone()

        cur = await self.conn.execute(
            """
            SELECT command_name, COUNT(*) AS uses, COUNT(DISTINCT user_id) AS unique_users
            FROM command_usage
            WHERE guild_id=? AND used_at >= ?
            GROUP BY command_name
            ORDER BY uses DESC, command_name ASC
            LIMIT 8
            """,
            (guild_id, since_epoch),
        )
        command_rows = await cur.fetchall()

        return {
            "sessions": int(sessions or 0),
            "active_users": int(active_users or 0),
            "seconds": int(seconds or 0),
            "active_now": int(active_now or 0),
            "weekly_recaps_sent": int(weekly_recaps_sent or 0),
            "inactivity_nudges_sent": int(inactivity_nudges_sent or 0),
            "achievements_awarded": int(achievements_awarded or 0),
            "new_voice_pairs": int(new_voice_pairs or 0),
            "partner_profiles_updated": int(partner_profiles_updated or 0),
            "commands": [(str(name), int(uses or 0), int(unique or 0)) for name, uses, unique in command_rows],
        }

    # -------------------------
    # Chat Jerry memory
    # -------------------------
    def _safe_json_dict(self, value: Any) -> dict[str, int]:
        if not isinstance(value, str) or not value.strip():
            return {}
        try:
            parsed = json.loads(value)
        except Exception:
            return {}
        if not isinstance(parsed, dict):
            return {}

        result: dict[str, int] = {}
        for key, count in parsed.items():
            try:
                result[str(key)] = max(0, int(count))
            except Exception:
                continue
        return result

    def _preferred_level_from_counts(self, counts: dict[str, int]) -> str | None:
        ordered_levels = ("starter", "easy", "growing", "strong")
        best_level: str | None = None
        best_count = 0
        for level in ordered_levels:
            count = int(counts.get(level, 0))
            if count > best_count:
                best_level = level
                best_count = count
        return best_level

    # -------------------------
    # KV
    # -------------------------
    async def kv_get(self, guild_id: int, key: str) -> str | None:
        cur = await self.conn.execute(
            "SELECT value FROM bot_kv WHERE guild_id=? AND key=?",
            (guild_id, key),
        )
        row = await cur.fetchone()
        return row[0] if row else None

    async def kv_set(self, guild_id: int, key: str, value: str) -> None:
        await self.conn.execute(
            """
            INSERT INTO bot_kv (guild_id, key, value)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id, key)
            DO UPDATE SET value=excluded.value
            """,
            (guild_id, key, value),
        )
        await self.conn.commit()

    # -------------------------
    # user_state
    # -------------------------
    async def user_state_get(self, guild_id: int, user_id: int) -> Dict[str, Any] | None:
        cur = await self.conn.execute(
            """
            SELECT last_voice_join_at, last_weekly_dm_week, last_weekly_dm_at, last_inactivity_nudge_at
            FROM user_state
            WHERE guild_id=? AND user_id=?
            """,
            (guild_id, user_id),
        )
        row = await cur.fetchone()
        if not row:
            return None
        return {
            "last_voice_join_at": row[0],
            "last_weekly_dm_week": row[1],
            "last_weekly_dm_at": row[2],
            "last_inactivity_nudge_at": row[3],
        }

    async def user_state_touch_voice_join(self, guild_id: int, user_id: int, at: int) -> None:
        await self.conn.execute(
            """
            INSERT INTO user_state (guild_id, user_id, last_voice_join_at)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id, user_id)
            DO UPDATE SET last_voice_join_at=excluded.last_voice_join_at
            """,
            (guild_id, user_id, at),
        )
        await self.conn.commit()

    async def user_state_mark_weekly_dm(self, guild_id: int, user_id: int, week_key: str, at: int) -> None:
        await self.conn.execute(
            """
            INSERT INTO user_state (guild_id, user_id, last_weekly_dm_week, last_weekly_dm_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(guild_id, user_id)
            DO UPDATE SET last_weekly_dm_week=excluded.last_weekly_dm_week,
                          last_weekly_dm_at=excluded.last_weekly_dm_at
            """,
            (guild_id, user_id, week_key, at),
        )
        await self.conn.commit()

    async def user_state_mark_inactivity_nudge(self, guild_id: int, user_id: int, at: int) -> None:
        await self.conn.execute(
            """
            INSERT INTO user_state (guild_id, user_id, last_inactivity_nudge_at)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id, user_id)
            DO UPDATE SET last_inactivity_nudge_at=excluded.last_inactivity_nudge_at
            """,
            (guild_id, user_id, at),
        )
        await self.conn.commit()

    # -------------------------
    # Achievements
    # -------------------------
    async def achievement_has(self, guild_id: int, user_id: int, achievement_id: str) -> bool:
        cur = await self.conn.execute(
            """
            SELECT 1
            FROM achievements
            WHERE guild_id=? AND user_id=? AND achievement_id=?
            LIMIT 1
            """,
            (guild_id, user_id, achievement_id),
        )
        row = await cur.fetchone()
        return bool(row)

    async def achievement_award_once(
        self,
        guild_id: int,
        user_id: int,
        achievement_id: str,
        earned_at: int | None = None,
    ) -> bool:
        """
        Returns True if newly inserted, False if already existed.
        """
        if earned_at is None:
            earned_at = int(time.time())

        try:
            await self.conn.execute(
                """
                INSERT INTO achievements (guild_id, user_id, achievement_id, earned_at)
                VALUES (?, ?, ?, ?)
                """,
                (guild_id, user_id, achievement_id, earned_at),
            )
            await self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Primary key conflict -> already earned
            return False

    async def achievement_revoke(self, guild_id: int, user_id: int, achievement_id: str) -> bool:
        cur = await self.conn.execute(
            """
            DELETE FROM achievements
            WHERE guild_id=? AND user_id=? AND achievement_id=?
            """,
            (guild_id, user_id, achievement_id),
        )
        await self.conn.commit()
        return cur.rowcount > 0

    async def achievements_list(self, guild_id: int, user_id: int) -> list[tuple[str, int]]:
        cur = await self.conn.execute(
            """
            SELECT achievement_id, earned_at
            FROM achievements
            WHERE guild_id=? AND user_id=?
            ORDER BY earned_at DESC
            """,
            (guild_id, user_id),
        )
        rows = await cur.fetchall()
        return [(str(aid), int(ts)) for (aid, ts) in rows]

    # -------------------------
    # voice_met (pair history)
    # -------------------------
    async def voice_met_add_if_new_pair(self, guild_id: int, user_id: int, other_user_id: int, at: int) -> bool:
        """
        Store canonical pair (min,max). Returns True if this is the first time they've met.
        """
        a = min(user_id, other_user_id)
        b = max(user_id, other_user_id)
        try:
            await self.conn.execute(
                """
                INSERT INTO voice_met (guild_id, user_a_id, user_b_id, first_met_at)
                VALUES (?, ?, ?, ?)
                """,
                (guild_id, a, b, at),
            )
            await self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    # -------------------------
    # Partner slots
    # -------------------------
    async def partner_slots_set(self, guild_id: int, user_id: int, slot_keys: list[str]) -> None:
        """Replace all slot selections for a user atomically."""
        now = int(time.time())
        await self.conn.execute(
            "DELETE FROM partner_slots WHERE guild_id=? AND user_id=?",
            (guild_id, user_id),
        )
        for key in slot_keys:
            await self.conn.execute(
                """
                INSERT INTO partner_slots (guild_id, user_id, slot_key, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(guild_id, user_id, slot_key)
                DO UPDATE SET updated_at=excluded.updated_at
                """,
                (guild_id, user_id, key, now),
            )
        await self.conn.commit()

    async def partner_slots_get(self, guild_id: int, user_id: int) -> list[str]:
        """Get all slot keys selected by a user."""
        cur = await self.conn.execute(
            "SELECT slot_key FROM partner_slots WHERE guild_id=? AND user_id=?",
            (guild_id, user_id),
        )
        rows = await cur.fetchall()
        return [r[0] for r in rows]

    async def partner_slots_find_matches(self, guild_id: int, slot_key: str, exclude_user_id: int) -> list[int]:
        """Find all users who have selected a given slot, excluding the caller."""
        cur = await self.conn.execute(
            """
            SELECT user_id FROM partner_slots
            WHERE guild_id=? AND slot_key=? AND user_id != ?
            """,
            (guild_id, slot_key, exclude_user_id),
        )
        rows = await cur.fetchall()
        return [r[0] for r in rows]

    async def partner_slots_get_all_for_slot(self, guild_id: int, slot_key: str) -> list[int]:
        """Get all user IDs who selected a given slot."""
        cur = await self.conn.execute(
            "SELECT user_id FROM partner_slots WHERE guild_id=? AND slot_key=?",
            (guild_id, slot_key),
        )
        rows = await cur.fetchall()
        return [r[0] for r in rows]
