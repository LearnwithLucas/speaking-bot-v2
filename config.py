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
