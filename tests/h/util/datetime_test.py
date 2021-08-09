import datetime

import pytest

from h.util.datetime import utc_iso8601, utc_us_style_date

TIMEZONE = datetime.timezone(offset=datetime.timedelta(hours=1), name="Berlin")


@pytest.mark.parametrize(
    "date,expected",
    (
        (
            datetime.datetime(2016, 2, 24, 18, 3, 25, 7685),
            "2016-02-24T18:03:25.007685+00:00",
        ),
        # We ignore timezones
        (
            datetime.datetime(2016, 2, 24, 18, 3, 25, 7685, TIMEZONE),
            "2016-02-24T18:03:25.007685+00:00",
        ),
        (None, None),
    ),
)
def test_utc_iso8601(date, expected):
    assert utc_iso8601(date) == expected


def test_utc_us_style_date():
    t = datetime.datetime(2016, 2, 4)
    assert utc_us_style_date(t) == "February 4, 2016"
