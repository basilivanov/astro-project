"""Date formatting helpers for backend utilities."""

from datetime import datetime, timezone


def format_iso_date(dt: datetime) -> str:
    """Format a datetime object as an ISO 8601 string."""
    return dt.isoformat()


def parse_iso_date(date_str: str) -> datetime:
    """Parse an ISO 8601 string into a datetime object."""
    normalized_date_str = date_str
    if date_str.endswith("Z"):
        normalized_date_str = f"{date_str[:-1]}+00:00"

    return datetime.fromisoformat(normalized_date_str)


def get_current_utc() -> datetime:
    """Return the current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)
