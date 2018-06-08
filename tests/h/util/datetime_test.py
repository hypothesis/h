# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

from h.util.datetime import utc_iso8601, utc_us_style_date


class Berlin(datetime.tzinfo):
    """Berlin timezone, without DST support"""

    def utcoffset(self, dt):
        return datetime.timedelta(hours=1)

    def tzname(self, dt):
        return "Berlin"

    def dst(self, dt):
        return datetime.timedelta()


def test_utc_iso8601():
    t = datetime.datetime(2016, 2, 24, 18, 3, 25, 7685)
    assert utc_iso8601(t) == "2016-02-24T18:03:25.007685+00:00"


def test_utc_iso8601_ignores_timezone():
    t = datetime.datetime(2016, 2, 24, 18, 3, 25, 7685, Berlin())
    assert utc_iso8601(t) == "2016-02-24T18:03:25.007685+00:00"


def test_utc_us_style_date():
    t = datetime.datetime(2016, 2, 4)
    assert utc_us_style_date(t) == "February 4, 2016"
