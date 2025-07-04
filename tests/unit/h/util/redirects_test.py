import pytest

from h.util.redirects import ParseError, Redirect, lookup, parse

WHITESPACE = " \t"


@pytest.mark.usefixtures("routes")
class TestLookup:
    def test_none_when_empty(self, pyramid_request):
        result = lookup([], pyramid_request)

        assert result is None

    def test_none_when_no_match(self, pyramid_request):
        pyramid_request.path = "/bar"
        redirects = [
            Redirect(
                src="/foo", dst="http://giraffe.com/bar", internal=False, prefix=False
            )
        ]

        result = lookup(redirects, pyramid_request)

        assert result is None

    def test_exact(self, pyramid_request):
        pyramid_request.path = "/foo"
        redirects = [
            Redirect(
                src="/foo", dst="http://giraffe.com/bar", internal=False, prefix=False
            )
        ]

        result = lookup(redirects, pyramid_request)

        assert result == "http://giraffe.com/bar"

    def test_prefix(self, pyramid_request):
        pyramid_request.path = "/foo/bar"
        redirects = [
            Redirect(src="/foo", dst="http://giraffe.com", internal=False, prefix=True)
        ]

        result = lookup(redirects, pyramid_request)

        assert result == "http://giraffe.com/bar"

    def test_internal_exact(self, pyramid_request):
        pyramid_request.path = "/foo"
        redirects = [Redirect(src="/foo", dst="donkey", internal=True, prefix=False)]

        result = lookup(redirects, pyramid_request)

        assert result == "http://example.com/donkey"

    def test_internal_prefix(self, pyramid_request):
        pyramid_request.path = "/foo/bar"
        redirects = [Redirect(src="/foo", dst="donkey", internal=True, prefix=True)]

        result = lookup(redirects, pyramid_request)

        assert result == "http://example.com/donkey/bar"

    def test_ordering_indicates_priority(self, pyramid_request):
        # Earlier matching redirect specifications should be chosen over later ones.
        pyramid_request.path = "/foo/bar"
        redirects = [
            Redirect(src="/foo", dst="http://giraffe.com", internal=False, prefix=True),
            Redirect(
                src="/foo/bar", dst="http://elephant.com", internal=False, prefix=False
            ),
        ]

        result = lookup(redirects, pyramid_request)

        assert result == "http://giraffe.com/bar"

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route("donkey", "/donkey")


class TestParse:
    def test_basic(self):
        result = parse(["/foo exact http://giraffe.com/bar"])

        assert result == [
            Redirect(
                src="/foo", dst="http://giraffe.com/bar", internal=False, prefix=False
            )
        ]

    def test_multiline(self):
        result = parse(
            [
                "/foo exact http://giraffe.com/bar",
                "/bar prefix http://elephant.org/",
                "/baz/bat internal-exact tapir",
                "/qux internal-prefix donkey",
            ]
        )

        assert result == [
            Redirect(
                src="/foo", dst="http://giraffe.com/bar", internal=False, prefix=False
            ),
            Redirect(
                src="/bar", dst="http://elephant.org/", internal=False, prefix=True
            ),
            Redirect(src="/baz/bat", dst="tapir", internal=True, prefix=False),
            Redirect(src="/qux", dst="donkey", internal=True, prefix=True),
        ]

    @pytest.mark.parametrize("maybe_empty_whitespace", ["", " ", "  \t"])
    @pytest.mark.parametrize("non_empty_whitespace", [" ", "   ", "\t"])
    def test_ignores_whitespace(self, maybe_empty_whitespace, non_empty_whitespace):
        line = [
            maybe_empty_whitespace,
            "/foo",
            non_empty_whitespace,
            "exact",
            non_empty_whitespace,
            "http://giraffe.com/bar",
            maybe_empty_whitespace,
        ]

        result = parse(["".join(line)])

        assert result == [
            Redirect(
                src="/foo", dst="http://giraffe.com/bar", internal=False, prefix=False
            )
        ]

    @pytest.mark.parametrize(
        "lines",
        [
            # Single empty lines
            [" "],
            ["\t"],
            ["\r"],
            [""],
            # Multiple empty lines
            [" ", "\t", "\r", ""],
        ],
    )
    def test_ignores_whitespace_only_lines(self, lines):
        result = parse(lines)

        assert not result

    @pytest.mark.parametrize(
        "line",
        [
            "foo",
            "#foo",
            "foo bar",
        ],
    )
    def test_ignores_comment_lines(self, line):
        result = parse(["#" + line])

        assert not result

    def test_misformatted_line_raises(self):
        with pytest.raises(ParseError) as e:
            parse(["/foo exact somethingelse http://giraffe.com/bar"])
        assert "invalid" in str(e.value)

    def test_unknown_type_raises(self):
        with pytest.raises(ParseError) as e:
            parse(["/foo magic http://giraffe.com/bar"])
        assert "type" in str(e.value)
