"""
ExamShield - Date Utilities

Provides timezone-aware datetime helpers for consistent timestamp
handling across the application.
"""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return the current datetime in UTC with timezone info."""
    return datetime.now(timezone.utc)


def to_utc(dt: datetime) -> datetime:
    """
    Convert a datetime to UTC.

    If the datetime is naive (no tzinfo), it is assumed to be UTC.
    If it has timezone info, it is converted to UTC.

    Args:
        dt: The datetime to convert.

    Returns:
        A timezone-aware datetime in UTC.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def format_iso(dt: datetime) -> str:
    """
    Format a datetime as an ISO 8601 string.

    Args:
        dt: The datetime to format.

    Returns:
        ISO 8601 formatted string.
    """
    return dt.isoformat()


def from_timestamp(ts: float) -> datetime:
    """
    Create a UTC datetime from a Unix timestamp.

    Args:
        ts: Unix timestamp (seconds since epoch).

    Returns:
        A timezone-aware datetime in UTC.
    """
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def elapsed_ms(start: datetime, end: datetime) -> float:
    """
    Calculate elapsed time in milliseconds between two datetimes.

    Args:
        start: Start datetime.
        end: End datetime.

    Returns:
        Elapsed time in milliseconds.
    """
    delta = end - start
    return delta.total_seconds() * 1000.0
