from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

EVENT_TZ = ZoneInfo("America/New_York")


def to_utc_naive(dt: datetime | date | None) -> datetime | None:
    """Normalize to naive UTC for storage (SQLite drops tzinfo; keep it consistent)."""
    if dt is None:
        return None
    if isinstance(dt, datetime):
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    return datetime(dt.year, dt.month, dt.day)


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def local_to_utc_naive(dt: datetime | None) -> datetime | None:
    """Interpret a naive datetime as US Eastern (what submitters mean) -> naive UTC."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=EVENT_TZ)
    return dt.astimezone(timezone.utc).replace(tzinfo=None)
