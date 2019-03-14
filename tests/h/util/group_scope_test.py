# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from h.util import group_scope as scope_util


class TestPatternForScope(object):
    @pytest.mark.parametrize(
        "scope,expected_pattern",
        [
            ("https://www.foo.com", "^https\\:\\/\\/www\\.foo\\.com.*"),
            ("http://foo.com", "^http\\:\\/\\/foo\\.com.*"),
            ("https://foo.com/bar", "^https\\:\\/\\/foo\\.com\\/bar.*"),
            (
                "http://www.foo.com/bar/baz.html",
                "^http\\:\\/\\/www\\.foo\\.com\\/bar\\/baz\\.html.*",
            ),
            ("foo", "^foo.*"),
            (None, "(?!x)x"),
        ],
    )
    def test_it_converts_uri_to_valid_pattern(self, scope, expected_pattern):
        assert scope_util.pattern_for_scope(scope) == expected_pattern


class TestURIInScope(object):
    @pytest.mark.parametrize(
        "scopes,expected_pattern",
        [
            (["foo", "bar", "baz"], "^foo.*|^bar.*|^baz.*"),
            (["http://bing.com/bar"], "^http\\:\\/\\/bing\\.com\\/bar.*"),
            (
                ["http://example.com/foo", "https://example.com/foo"],
                "^http\\:\\/\\/example\\.com\\/foo.*|^https\\:\\/\\/example\\.com\\/foo.*",
            ),
        ],
    )
    def test_it_creates_valid_single_pattern_string(
        self, scopes, expected_pattern, match
    ):
        scope_util.uri_in_scope("http://foo.com", scopes)

        match.assert_called_once_with(expected_pattern, "http://foo.com")

    @pytest.mark.parametrize(
        "uri,in_origin,in_path,in_other",
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
    def test_it_returns_True_if_uri_matches_one_or_more_scopes(
        self, scope_lists, uri, in_origin, in_path, in_other
    ):
        assert scope_util.uri_in_scope(uri, scope_lists["origin_only"]) == in_origin
        assert scope_util.uri_in_scope(uri, scope_lists["with_path"]) == in_path
        assert scope_util.uri_in_scope(uri, scope_lists["with_other"]) == in_other

    @pytest.fixture
    def match(self, patch):
        return patch("h.util.group_scope.re.match")

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


class TestURIToScope(object):
    @pytest.mark.parametrize(
        "uri,expected_scope",
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
    def test_it_parses_origin_and_path_from_uri(self, uri, expected_scope):
        assert scope_util.uri_to_scope(uri) == expected_scope


class TestParseOrigin(object):
    @pytest.mark.parametrize(
        "uri,expected_origin",
        [
            ("https://www.foo.com/foo/qux/bar.html", "https://www.foo.com"),
            ("http://foo.com/baz", "http://foo.com"),
            ("http://foo.com:3553/bar", "http://foo.com:3553"),
            ("http://www.foo.bar.com", "http://www.foo.bar.com"),
            ("foo.com", None),
        ],
    )
    def test_it_parses_origin_from_uri(self, uri, expected_origin):
        assert scope_util.parse_origin(uri) == expected_origin
