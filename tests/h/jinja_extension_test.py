# -*- coding: utf-8 -*-

import datetime

from jinja2 import Markup
import pytest

from h import jinja_extensions as ext
from h._compat import StringIO

@pytest.mark.parametrize("value_in,json_out", [
    ({"foo": 42}, "{\"foo\": 42}")
])
def test_to_json(value_in, json_out):
    result = str(ext.to_json(value_in))

    assert result == json_out


@pytest.mark.parametrize("timestamp_in,string_out", [
    # Basic format for recent timestamps
    (datetime.datetime(2016, 4, 14, 16, 45, 36, 529730),
     '14 April at 16:45'),
    # For times more than a year ago, add the year
    (datetime.datetime(2012, 4, 14, 16, 45, 36, 529730),
     '14 April 2012 at 16:45'),
])
def test_human_timestamp(timestamp_in, string_out):
    result = ext.human_timestamp(
        timestamp_in, now=lambda: datetime.datetime(2016, 4, 14))

    assert result == string_out


def test_svg_icon_loads_icon():
    def read_icon(name):
        return StringIO('<svg><!-- {} !--></svg>'.format(name))

    result = ext.svg_icon(read_icon, 'settings')

    assert result == Markup('<svg><!-- settings !--></svg>')


def test_svg_icon_removes_title():
    def read_icon(name):
        return StringIO('<svg><title>foo</title></svg>')

    assert ext.svg_icon(read_icon, 'icon') == Markup('<svg/>')


def test_svg_icon_sets_css_class():
    def read_icon(name):
        return StringIO('<svg></svg>')

    result = ext.svg_icon(read_icon, 'icon', css_class='fancy-icon')

    assert result == Markup('<svg class="fancy-icon"/>')
