# -*- coding: utf-8 -*-

import datetime

import pytest

from h import jinja_extensions as ext


@pytest.mark.parametrize("value_in,json_out", [
  ({"foo": 42}, "{\"foo\": 42}")
])
def test_to_json(value_in, json_out):
    result = str(ext.to_json(value_in))

    assert result == json_out


@pytest.mark.parametrize("timestamp_in,string_out", [
    # Basic format for recent timestamps
    (datetime.datetime(2016, 4, 14, 16, 45, 36, 529730), '14 April at 16:45'),
    # For times more than a year ago, add the year
    (datetime.datetime(2012, 4, 14, 16, 45, 36, 529730), '14 April 2012 at 16:45'),
])
def test_human_timestamp(timestamp_in, string_out):
    result = ext.human_timestamp(timestamp_in,
                                 now=lambda: datetime.datetime(2016, 4, 14))

    assert result == string_out
