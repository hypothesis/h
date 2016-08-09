# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from memex import markdown


def test_render_renders_markdown():
    actual = markdown.render('_emphasis_ **bold**')
    assert '<p><em>emphasis</em> <strong>bold</strong></p>\n' == actual
