import pytest

from h.util import markdown


class TestRender:
    def test_it_renders_markdown(self):
        actual = markdown.render("_emphasis_ **bold**")
        assert actual == "<p><em>emphasis</em> <strong>bold</strong></p>\n"

    def test_it_ignores_math_block(self):
        actual = markdown.render("$$1 + 1 = 2$$")
        assert actual == "<p>$$1 + 1 = 2$$</p>\n"

    def test_it_ignores_inline_math(self):
        actual = markdown.render(r"Foobar \(1 + 1 = 2\)")
        assert actual == "<p>Foobar \\(1 + 1 = 2\\)</p>\n"

    def test_it_sanitizes_the_output(self, markdown_render, sanitize):
        markdown.render("foobar")
        sanitize.assert_called_once_with(markdown_render.return_value.return_value)

    @pytest.fixture
    def markdown_render(self, patch):
        return patch("h.util.markdown._get_markdown")

    @pytest.fixture
    def sanitize(self, patch):
        return patch("h.util.markdown.sanitize")


class TestSanitize:
    @pytest.mark.parametrize(
        "text",
        [
            '<a href="mailto:foo@example.net">example</a>',  # Don't add rel and target attrs to mailto: links
            '<a title="foobar">example</a>',
            '<a href="https://example.org" rel="nofollow noopener" target="_blank" title="foobar">example</a>',
            "<blockquote>Foobar</blockquote>",
            "<code>foobar</code>",
            "<em>foobar</em>",
            "<hr>",
            "<h1>foobar</h1>",
            "<h2>foobar</h2>",
            "<h3>foobar</h3>",
            "<h4>foobar</h4>",
            "<h5>foobar</h5>",
            "<h6>foobar</h6>",
            '<img src="http://example.com/img.jpg">',
            '<img src="/img.jpg">',
            '<img alt="foobar" src="/img.jpg">',
            '<img src="/img.jpg" title="foobar">',
            '<img alt="hello" src="/img.jpg" title="foobar">',
            "<ol><li>foobar</li></ol>",
            "<p>foobar</p>",
            "<pre>foobar</pre>",
            "<strong>foobar</strong>",
            "<ul><li>foobar</li></ul>",
        ],
    )
    def test_it_allows_markdown_html(self, text):
        # HTML tags that Markdown can output are allowed through unsanitized.
        assert markdown.sanitize(text) == text

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
