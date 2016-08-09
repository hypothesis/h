# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from memex import markdown


def test_render_renders_markdown():
    actual = markdown.render('_emphasis_ **bold**')
    assert '<p><em>emphasis</em> <strong>bold</strong></p>\n' == actual


def test_render_ignores_math_block():
    actual = markdown.render('$$1 + 1 = 2$$')
    assert '<p>$$1 + 1 = 2$$</p>\n' == actual


def test_render_ignores_inline_match():
    actual = markdown.render('Foobar \(1 + 1 = 2\)')
    assert '<p>Foobar \(1 + 1 = 2\)</p>\n' == actual
