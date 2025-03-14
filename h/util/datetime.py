"""Shared utility functions for manipulating dates and times."""  # noqa: A005


def utc_iso8601(datetime):
    """Convert a UTC datetime into an ISO8601 timestamp string."""

    if not datetime:
        return None

    return datetime.strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")


def utc_us_style_date(datetime):
    """Convert a UTC datetime into a Month day, year (August 1, 1990)."""
    return f"{datetime:%B} {datetime.day}, {datetime:%Y}"
