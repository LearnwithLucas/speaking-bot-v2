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

-- Member joins per server, for the "in voice within 7 days" activation stat.
-- Kept after a member leaves, so the stat also counts people who churned.
CREATE TABLE IF NOT EXISTS member_joins (
  guild_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  joined_at INTEGER NOT NULL,       -- epoch seconds, most recent join
  PRIMARY KEY (guild_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_member_joins_time
  ON member_joins (guild_id, joined_at);

-- Speaking level per member, for partner matching (same level only).
CREATE TABLE IF NOT EXISTS member_levels (
  guild_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  level TEXT NOT NULL,              -- "A2", "B1" or "B2"
  updated_at INTEGER NOT NULL,
  PRIMARY KEY (guild_id, user_id)
);

-- Conversation Host invites (sent once per member, at 20h of voice time).
CREATE TABLE IF NOT EXISTS host_invites (
  guild_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  invited_at INTEGER NOT NULL,
  answer TEXT,                      -- NULL (no answer yet), "yes" or "not_now"
  answered_at INTEGER,
  decision TEXT,                    -- NULL, "approved" or "declined" (Lucas)
  decided_at INTEGER,
  decided_by INTEGER,
  PRIMARY KEY (guild_id, user_id)
);

-- Public milestone shout-outs: one row per member per milestone, ever.
CREATE TABLE IF NOT EXISTS milestone_announcements (
  guild_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  milestone TEXT NOT NULL,          -- "1h", "3h", "10h", "20h", "50h", "100h"
  announced_at INTEGER NOT NULL,
  posted INTEGER NOT NULL DEFAULT 1, -- 0 = marked done without a post (seeded at deploy)
  PRIMARY KEY (guild_id, user_id, milestone)
);

CREATE INDEX IF NOT EXISTS idx_milestone_announcements_time
  ON milestone_announcements (guild_id, announced_at);

-- Per-member settings. Shout-outs are on unless a row says 0.
CREATE TABLE IF NOT EXISTS member_settings (
  guild_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  milestone_shoutouts_enabled INTEGER NOT NULL DEFAULT 1,
  updated_at INTEGER NOT NULL,
  PRIMARY KEY (guild_id, user_id)
);

-- Admin-only health summaries: broad command usage, no message content.
CREATE TABLE IF NOT EXISTS command_usage (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  guild_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  command_name TEXT NOT NULL,
  used_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_command_usage_time
  ON command_usage (guild_id, command_name, used_at);

-- Chat Jerry memory: aggregate preferences only, no raw chat text.
-- Chat with Jerry was removed; its per-member topic memory goes with it.
DROP TABLE IF EXISTS chat_jerry_memory;
"""
