from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def round_seconds_to_nearest_minute(seconds: int) -> int:
    if seconds <= 0:
        return 0
    return int((seconds / 60.0) + 0.5)


def clamp_non_negative(n: int) -> int:
    return n if n > 0 else 0


def _amsterdam_now() -> dt.datetime:
    try:
        tz = ZoneInfo("Europe/Amsterdam")
        return dt.datetime.now(tz=tz)
    except ZoneInfoNotFoundError:
        return dt.datetime.now()


def amsterdam_iso_week_key(now: dt.datetime | None = None) -> str:
    """
    Returns ISO week key for Europe/Amsterdam, like "2025-W52".
    Falls back to local time if tzdata is unavailable.
    """
    if now is None:
        now = _amsterdam_now()
    iso = now.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def amsterdam_day_key(now: dt.datetime | None = None) -> str:
    """
    Returns day key for Europe/Amsterdam, like "2025-12-29".
    Falls back to local time if tzdata is unavailable.
    """
    if now is None:
        now = _amsterdam_now()
    return now.date().isoformat()


def amsterdam_day_key_from_epoch(epoch_seconds: int) -> str:
    """
    Convert an epoch timestamp into an Amsterdam day key ("YYYY-MM-DD").
    Falls back to local time if tzdata is unavailable.
    """
    try:
        tz = ZoneInfo("Europe/Amsterdam")
        dt_local = dt.datetime.fromtimestamp(epoch_seconds, tz=tz)
    except ZoneInfoNotFoundError:
        dt_local = dt.datetime.fromtimestamp(epoch_seconds)
    return dt_local.date().isoformat()
