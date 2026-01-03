from datetime import datetime, timezone


def get_current_utc_time() -> datetime:
    """
    Returns the current time in UTC as a timezone-aware datetime object.
    Use this function throughout the codebase for consistent UTC time handling.
    """
    return datetime.now(timezone.utc)
