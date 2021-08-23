from datetime import datetime

import pytest

from h.jinja_extensions.filters import format_number, human_timestamp, to_json


@pytest.mark.parametrize(
    "value_in,json_out",
    [
        ({"foo": 42}, '{"foo": 42}'),
        # to_json should escape HTML tags so that the result can be safely included
        # in HTML, eg. for encoding data payloads that are used by JavaScript code
        # on the page.
        ("<html-tag>&'", '"\\u003chtml-tag\\u003e\\u0026\\u0027"'),
        (
            '</script><script>alert("foo")</script>',
            '"\\u003c/script\\u003e\\u003cscript\\u003ealert(\\"foo\\")\\u003c/script\\u003e"',
        ),
    ],
)
def test_to_json(value_in, json_out):
    assert str(to_json(value_in)) == json_out


@pytest.mark.parametrize(
    "timestamp_in,string_out",
    [
        # Basic format for recent timestamps
        (datetime(2016, 4, 14, 16, 45, 36, 529730), "14 April at 16:45"),
        # For times more than a year ago, add the year
        (datetime(2012, 4, 14, 16, 45, 36, 529730), "14 April 2012 at 16:45"),
    ],
)
def test_human_timestamp(timestamp_in, string_out):
    assert (
        human_timestamp(timestamp_in, now=lambda: datetime(2016, 4, 14)) == string_out
    )


def test_format_number():
    assert format_number(134908) == "134,908"
