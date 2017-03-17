# -*- coding: utf-8 -*-

"""Shared utility functions for manipulating dates and times."""


def utc_iso8601(datetime):
    """Convert a UTC datetime into an ISO8601 timestamp string."""
    return datetime.strftime('%Y-%m-%dT%H:%M:%S.%f+00:00')
