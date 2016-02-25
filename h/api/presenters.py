# -*- coding: utf-8 -*-
"""
Presenters for API data.
"""

import collections


def utc_iso8601(datetime):
    return datetime.strftime('%Y-%m-%dT%H:%M:%S.%f+00:00')


def deep_merge_dict(a, b):
    """Recursively merges dict `b` into dict `a`."""

    for k, v in b.items():
        if isinstance(v, collections.Mapping):
            if k not in a or not isinstance(a[k], dict):
                a[k] = dict()
            deep_merge_dict(a[k], v)
        else:
            a[k] = v
