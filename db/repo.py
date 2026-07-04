import aiosqlite
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
        await self.end_open_session(guild_id, user_id, ended_at=started_at)
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