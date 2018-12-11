# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import datetime

from jinja2 import Markup
import pytest

from h import jinja_extensions as ext


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
    result = str(ext.to_json(value_in))

    assert result == json_out


@pytest.mark.parametrize(
    "timestamp_in,string_out",
    [
        # Basic format for recent timestamps
        (datetime.datetime(2016, 4, 14, 16, 45, 36, 529730), "14 April at 16:45"),
        # For times more than a year ago, add the year
        (datetime.datetime(2012, 4, 14, 16, 45, 36, 529730), "14 April 2012 at 16:45"),
    ],
)
def test_human_timestamp(timestamp_in, string_out):
    result = ext.human_timestamp(
        timestamp_in, now=lambda: datetime.datetime(2016, 4, 14)
    )

    assert result == string_out


def test_format_number():
    num = 134908
    result = ext.format_number(num)
    assert result == "134,908"


def test_svg_icon_loads_icon():
    def read_icon(name):
        return '<svg id="{}"></svg>'.format(name)

    result = ext.svg_icon(read_icon, "settings")

    assert result == Markup('<svg class="svg-icon" id="settings" />')


def test_svg_icon_removes_title():
    def read_icon(name):
        return '<svg xmlns="http://www.w3.org/2000/svg"><title>foo</title></svg>'

    assert ext.svg_icon(read_icon, "icon") == Markup(
        '<svg xmlns="http://www.w3.org/2000/svg" class="svg-icon" />'
    )


def test_svg_icon_strips_default_xml_namespace():
    def read_icon(name):
        return '<svg xmlns="http://www.w3.org/2000/svg"></svg>'

    assert ext.svg_icon(read_icon, "icon") == Markup(
        '<svg xmlns="http://www.w3.org/2000/svg" class="svg-icon" />'
    )


def test_svg_icon_sets_css_class():
    def read_icon(name):
        return "<svg></svg>"

    result = ext.svg_icon(read_icon, "icon", css_class="fancy-icon")

    assert result == Markup('<svg class="svg-icon fancy-icon" />')
