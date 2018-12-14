# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.util import markdown


class TestRender(object):
    def test_it_renders_markdown(self):
        actual = markdown.render("_emphasis_ **bold**")
        assert "<p><em>emphasis</em> <strong>bold</strong></p>\n" == actual

    def test_it_ignores_math_block(self):
        actual = markdown.render("$$1 + 1 = 2$$")
        assert "<p>$$1 + 1 = 2$$</p>\n" == actual

    def test_it_ignores_inline_match(self):
        actual = markdown.render(r"Foobar \(1 + 1 = 2\)")
        assert "<p>Foobar \\(1 + 1 = 2\\)</p>\n" == actual

    def test_it_sanitizes_the_output(self, markdown_render, sanitize):
        markdown.render("foobar")
        sanitize.assert_called_once_with(markdown_render.return_value)

    @pytest.fixture
    def markdown_render(self, patch):
        return patch("h.util.markdown.markdown")

    @pytest.fixture
    def sanitize(self, patch):
        return patch("h.util.markdown.sanitize")


class TestSanitize(object):
    @pytest.mark.parametrize(
        "text,expected",
        [
            (
                '<a href="https://example.org">example</a>',
                '<a href="https://example.org" rel="nofollow noopener" target="_blank">example</a>',
            ),
            # Don't add rel and target attrs to mailto: links
            ('<a href="mailto:foo@example.net">example</a>', None),
            ('<a title="foobar">example</a>', None),
            (
                '<a href="https://example.org" rel="nofollow noopener" target="_blank" title="foobar">example</a>',
                None,
            ),
            ("<blockquote>Foobar</blockquote>", None),
            ("<code>foobar</code>", None),
            ("<em>foobar</em>", None),
            ("<hr>", None),
            ("<h1>foobar</h1>", None),
            ("<h2>foobar</h2>", None),
            ("<h3>foobar</h3>", None),
            ("<h4>foobar</h4>", None),
            ("<h5>foobar</h5>", None),
            ("<h6>foobar</h6>", None),
            ('<img src="http://example.com/img.jpg">', None),
            ('<img src="/img.jpg">', None),
            ('<img alt="foobar" src="/img.jpg">', None),
            ('<img src="/img.jpg" title="foobar">', None),
            ('<img alt="hello" src="/img.jpg" title="foobar">', None),
            ("<ol><li>foobar</li></ol>", None),
            ("<p>foobar</p>", None),
            ("<pre>foobar</pre>", None),
            ("<strong>foobar</strong>", None),
            ("<ul><li>foobar</li></ul>", None),
        ],
    )
    def test_it_allows_markdown_html(self, text, expected):
        if expected is None:
            expected = text

        assert markdown.sanitize(text) == expected

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("<script>evil()</script>", "&lt;script&gt;evil()&lt;/script&gt;"),
            (
                '<a href="#" onclick="evil()">foobar</a>',
                '<a href="#" rel="nofollow noopener" target="_blank">foobar</a>',
            ),
            (
                '<a href="#" onclick=evil()>foobar</a>',
                '<a href="#" rel="nofollow noopener" target="_blank">foobar</a>',
            ),
            ("<a href=\"javascript:alert('evil')\">foobar</a>", "<a>foobar</a>"),
            ('<img src="/evil.jpg" onclick="evil()">', '<img src="/evil.jpg">'),
            ("<img src=\"javascript:alert('evil')\">", "<img>"),
        ],
    )
    def test_it_escapes_evil_html(self, text, expected):
        assert markdown.sanitize(text) == expected

    def test_it_adds_target_blank_and_rel_nofollow_to_links(self):
        actual = markdown.sanitize('<a href="https://example.org">Hello</a>')
        expected = '<a href="https://example.org" rel="nofollow noopener" target="_blank">Hello</a>'

        assert actual == expected
