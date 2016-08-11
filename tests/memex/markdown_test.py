# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from memex import markdown


class TestRender(object):
    def test_it_renders_markdown(self):
        actual = markdown.render('_emphasis_ **bold**')
        assert '<p><em>emphasis</em> <strong>bold</strong></p>\n' == actual

    def test_it_ignores_math_block(self):
        actual = markdown.render('$$1 + 1 = 2$$')
        assert '<p>$$1 + 1 = 2$$</p>\n' == actual

    def test_it_ignores_inline_match(self):
        actual = markdown.render('Foobar \(1 + 1 = 2\)')
        assert '<p>Foobar \(1 + 1 = 2\)</p>\n' == actual

    def test_it_sanitizes_the_output(self, markdown_render, sanitize):
        markdown.render('foobar')
        sanitize.assert_called_once_with(markdown_render.return_value)

    @pytest.fixture
    def markdown_render(self, patch):
        return patch('memex.markdown.markdown')

    @pytest.fixture
    def sanitize(self, patch):
        return patch('memex.markdown.sanitize')


class TestSanitize(object):
    @pytest.mark.parametrize("text", [
        '<a href="https://example.org">example</a>',
        '<a title="foobar">example</a>',
        '<a href="https://example.org" title="foobar">example</a>',
        '<blockquote>Foobar</blockquote>',
        '<code>foobar</code>',
        '<em>foobar</em>',
        '<hr>',
        '<h1>foobar</h1>'
        '<h2>foobar</h2>'
        '<h3>foobar</h3>'
        '<h4>foobar</h4>',
        '<h5>foobar</h5>',
        '<h6>foobar</h6>',
        '<img src="http://example.com/img.jpg">',
        '<img src="/img.jpg">',
        '<img alt="foobar" src="/img.jpg">',
        '<img src="/img.jpg" title="foobar">',
        '<img alt="hello" src="/img.jpg" title="foobar">',
        '<ol><li>foobar</li></ol>',
        '<p>foobar</p>'
        '<pre>foobar</pre>',
        '<strong>foobar</strong>',
        '<ul><li>foobar</li></ul>',
    ])
    def test_it_allows_markdown_html(self, text):
        assert markdown.sanitize(text) == text

    @pytest.mark.parametrize("text,expected", [
        ('<script>evil()</script>', '&lt;script&gt;evil()&lt;/script&gt;'),
        ('<a href="#" onclick="evil()">foobar</a>', '<a href="#">foobar</a>'),
        ('<a href="#" onclick=evil()>foobar</a>', '<a href="#">foobar</a>'),
        ('<a href="javascript:alert(\'evil\')">foobar</a>', '<a>foobar</a>'),
        ('<img src="/evil.jpg" onclick="evil()">', '<img src="/evil.jpg">'),
        ('<img src="javascript:alert(\'evil\')">', '<img>'),
    ])
    def test_it_escapes_evil_html(self, text, expected):
        assert markdown.sanitize(text) == expected

    def test_it_adds_target_blank_to_links(self):
        actual = markdown.sanitize('<a href="https://example.org">Hello</a>')

        assert actual == '<a href="https://example.org" target="_blank">Hello</a>'
