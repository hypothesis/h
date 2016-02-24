# -*- coding: utf-8 -*-
"""
Presenters for API data.
"""


def utc_iso8601(datetime):
    return datetime.strftime('%Y-%m-%dT%H:%M:%S.%f+00:00')
