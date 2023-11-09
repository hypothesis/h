import pytest

from h.util import group_scope as scope_util


class TestURLInScope:
    @pytest.mark.parametrize(
        "url,in_origin,in_path,in_other",
        [
            ("https://www.foo.com", True, False, False),
            ("http://foo.com", False, False, False),
            ("http://www.foo.com/bar/qux.html", True, True, True),
            ("http://www.foo.com/bar/baz/qux.html", True, True, True),
            ("http://foo.com/", False, False, False),
            ("http://www.foo.com/bar.baz", True, False, False),
            ("www.foo.com", False, False, False),
            ("randoscheme://foo.com", False, False, False),
            ("foo", False, False, False),
            ("https://www.foo.com/bar/baz", True, False, False),
            ("", False, False, False),
        ],
    )
    def test_it_returns_True_if_url_matches_one_or_more_scopes(
        self, scope_lists, url, in_origin, in_path, in_other
    ):
        assert scope_util.url_in_scope(url, scope_lists["origin_only"]) == in_origin
        assert scope_util.url_in_scope(url, scope_lists["with_path"]) == in_path
        assert scope_util.url_in_scope(url, scope_lists["with_other"]) == in_other

    @pytest.fixture
    def scope_lists(self):
        return {
            "origin_only": ["http://www.foo.com", "https://www.foo.com"],
            "with_path": [
                "http://www.foo.com/bar/baz",
                "http://www.foo.com/bar/qux",
                "http://www.foo.com/bar/baz/qux",
            ],
            "with_other": [
                "http://www.foo.com/bar/baz/qux.html",
                "http://www.foo.com/bar/qux",
            ],
        }


class TestParseURLFromScope:
    @pytest.mark.parametrize(
        "url,expected_scope",
        [
            ("https://www.foo.com/foo", ("https://www.foo.com", "/foo")),
            ("https://foo.com/bar/baz", ("https://foo.com", "/bar/baz")),
            ("http://foo.com", ("http://foo.com", None)),
            ("/foo/bar", (None, "/foo/bar")),
            (
                "https://foo.com/foo/bar/baz.html",
                ("https://foo.com", "/foo/bar/baz.html"),
            ),
            ("http://foo.com//bar/baz", ("http://foo.com", "//bar/baz")),
            ("http://foo.com/bar?what=how", ("http://foo.com", "/bar")),
        ],
    )
    def test_it_parses_origin_and_path_from_url(self, url, expected_scope):
        assert scope_util.parse_scope_from_url(url) == expected_scope


class TestParseOrigin:
    @pytest.mark.parametrize(
        "url,expected_origin",
        [
            ("https://www.foo.com/foo/qux/bar.html", "https://www.foo.com"),
            ("http://foo.com/baz", "http://foo.com"),
            ("http://foo.com:3553/bar", "http://foo.com:3553"),
            ("http://www.foo.bar.com", "http://www.foo.bar.com"),
            # URLs with missing scheme or host.
            ("file:///apath", None),
            ("foo:123", None),
            ("bar:", None),
            ("foo.com", None),
        ],
    )
    def test_it_parses_origin_from_url(self, url, expected_origin):
        assert scope_util.parse_origin(url) == expected_origin
