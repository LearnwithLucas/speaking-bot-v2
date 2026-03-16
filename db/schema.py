SCHEMA_SQL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS voice_sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  guild_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  channel_id INTEGER NOT NULL,
  started_at INTEGER NOT NULL,      -- epoch seconds
  ended_at INTEGER                 -- epoch seconds, NULL means open
);

CREATE INDEX IF NOT EXISTS idx_sessions_open
  ON voice_sessions (guild_id, user_id)
  WHERE ended_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_sessions_time
  ON voice_sessions (guild_id, started_at, ended_at);

CREATE TABLE IF NOT EXISTS speaking_cache (
  guild_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  total_seconds INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (guild_id, user_id)
);

CREATE TABLE IF NOT EXISTS bot_kv (
  guild_id INTEGER NOT NULL,
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  PRIMARY KEY (guild_id, key)
);

CREATE TABLE IF NOT EXISTS user_state (
  guild_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,

  -- Most recent qualifying "entered voice" (epoch seconds)
  last_voice_join_at INTEGER,

  -- Weekly DM rate limit
  last_weekly_dm_week TEXT,         -- e.g. "2026-W01" (timezone-aware key)
  last_weekly_dm_at INTEGER,        -- epoch seconds

  -- Inactivity nudge rate limit (Step 6, default OFF)
  last_inactivity_nudge_at INTEGER, -- epoch seconds

  PRIMARY KEY (guild_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_user_state_voice_join
  ON user_state (guild_id, last_voice_join_at);

CREATE TABLE IF NOT EXISTS achievements (
  guild_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  achievement_id TEXT NOT NULL,
  earned_at INTEGER NOT NULL,
  PRIMARY KEY (guild_id, user_id, achievement_id)
);

CREATE INDEX IF NOT EXISTS idx_achievements_user
  ON achievements (guild_id, user_id);

-- Voice met (pair history for achievements)
CREATE TABLE IF NOT EXISTS voice_met (
  guild_id INTEGER NOT NULL,
  user_a_id INTEGER NOT NULL,
  user_b_id INTEGER NOT NULL,
  first_met_at INTEGER NOT NULL,
  PRIMARY KEY (guild_id, user_a_id, user_b_id)
);

-- Partner finder: stores which slots each user has selected
CREATE TABLE IF NOT EXISTS partner_slots (
  guild_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  slot_key TEXT NOT NULL,           -- e.g. "mon_after_stream", "daily_morning"
  updated_at INTEGER NOT NULL,      -- epoch seconds
  PRIMARY KEY (guild_id, user_id, slot_key)
);

CREATE INDEX IF NOT EXISTS idx_partner_slots_slot
  ON partner_slots (guild_id, slot_key);
"""