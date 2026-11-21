from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


def _parse_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    v = value.strip().lower()
    if v in {"1", "true", "yes", "y", "on"}:
        return True
    if v in {"0", "false", "no", "n", "off"}:
        return False
    return default


@dataclass(frozen=True)
class Settings:
    discord_token: str
    guild_id: int

    speak_now_category_id: int
    announcements_channel_id: int

    # Dutch server
    dutch_guild_id: int | None

    # Role assignment on join
    english_learner_role_id: int

    # Optional explicit AFK channel exclusion
    afk_channel_id: int | None

    # Step 4 config
    nudge_days: str
    nudge_time: str

    # Safety flags
    debug_commands: bool
    enable_inactivity_nudge: bool
    inactivity_nudge_variant: str

    # Storage/logging
    db_path: str
    log_level: str = "INFO"


def get_settings() -> Settings:
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        raise RuntimeError("DISCORD_TOKEN is missing in .env")

    def req_int(name: str) -> int:
        raw = os.getenv(name, "").strip()
        if not raw:
            raise RuntimeError(f"{name} is missing in .env")
        return int(raw)

    def opt_int(name: str) -> int | None:
        raw = os.getenv(name, "").strip()
        return int(raw) if raw else None

    return Settings(
        discord_token=token,
        guild_id=req_int("GUILD_ID"),
        dutch_guild_id=opt_int("DUTCH_GUILD_ID"),
        speak_now_category_id=req_int("SPEAK_NOW_CATEGORY_ID"),
        announcements_channel_id=req_int("ANNOUNCEMENTS_CHANNEL_ID"),
        english_learner_role_id=req_int("ENGLISH_LEARNER_ROLE_ID"),
        afk_channel_id=opt_int("AFK_CHANNEL_ID"),
        nudge_days=os.getenv("NUDGE_DAYS", "MON,FRI").strip(),
        nudge_time=os.getenv("NUDGE_TIME", "15:00").strip(),
        debug_commands=_parse_bool(os.getenv("DEBUG_COMMANDS", "0"), default=False),
        enable_inactivity_nudge=_parse_bool(os.getenv("ENABLE_INACTIVITY_NUDGE", "false"), default=False),
        inactivity_nudge_variant=os.getenv("INACTIVITY_NUDGE_VARIANT", "A").strip().upper(),
        db_path=os.getenv("DB_PATH", "botlab_speaking.sqlite").strip(),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
    )

# -------------------------
# Role IDs (EN server). Fill in the IDs, or set the env var of the same
# name on Render. 0 = not set: that role is skipped.
# -------------------------
def _role_id(name: str, default: int = 0) -> int:
    raw = os.getenv(name, "").strip()
    try:
        return int(raw) if raw else default
    except ValueError:
        return default


# Voice time (seconds, counted from the milestone start) -> role ID.
# A member holds only the highest one they reached.
MILESTONE_ROLES: tuple[tuple[int, str, int], ...] = (
    (15 * 60, "First Words", _role_id("MILESTONE_ROLE_15M")),
    (1 * 3600, "1 hour", _role_id("MILESTONE_ROLE_1H")),
    (3 * 3600, "3 hours", _role_id("MILESTONE_ROLE_3H")),
    (10 * 3600, "10 hours", _role_id("MILESTONE_ROLE_10H")),
    (20 * 3600, "20 hours", _role_id("MILESTONE_ROLE_20H")),
    (50 * 3600, "50 hours", _role_id("MILESTONE_ROLE_50H")),
    (100 * 3600, "Speaker", _role_id("MILESTONE_ROLE_100H")),
)

CONVERSATION_HOST_ROLE_ID: int = _role_id("CONVERSATION_HOST_ROLE_ID")

# Channel for public milestone shout-outs (#your-successes-and-stories).
# Empty = no shout-outs.
MILESTONE_ANNOUNCE_CHANNEL_ID: int = _role_id("MILESTONE_ANNOUNCE_CHANNEL_ID")
