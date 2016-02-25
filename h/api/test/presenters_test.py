# -*- coding: utf-8 -*-

import datetime

from h.api.presenters import utc_iso8601, deep_merge_dict


def test_utc_iso8601():
    t = datetime.datetime(2016, 2, 24, 18, 03, 25, 7685)
    assert utc_iso8601(t) == '2016-02-24T18:03:25.007685+00:00'


def test_utc_iso8601_ignores_timezone():
    t = datetime.datetime(2016, 2, 24, 18, 03, 25, 7685, Berlin())
    assert utc_iso8601(t) == '2016-02-24T18:03:25.007685+00:00'


def test_deep_merge_dict():
    a = {'foo': 1, 'bar': 2, 'baz': {'foo': 3, 'bar': 4}}
    b = {'bar': 8, 'baz': {'bar': 6, 'qux': 7}, 'qux': 15}
    deep_merge_dict(a, b)

    assert a == {
        'foo': 1,
        'bar': 8,
        'baz': {
            'foo': 3,
            'bar': 6,
            'qux': 7},
        'qux': 15}


class Berlin(datetime.tzinfo):
    """Berlin timezone, without DST support"""

    def utcoffset(self, dt):
        return datetime.timedelta(hours=1)

    def tzname(self, dt):
        return "Berlin"

    def dst(self, dt):
        return datetime.timedelta()
