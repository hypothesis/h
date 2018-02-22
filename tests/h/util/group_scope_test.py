# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from h.util import group_scope as scope_util


@pytest.mark.parametrize('uri,expected_scope', [
    ('https://www.foo.com', 'https://www.foo.com'),
    ('http://foo.com', 'http://foo.com'),
    ('https://foo.com/bar', 'https://foo.com'),
    ('http://foo.com/', 'http://foo.com'),
    ('http://www.foo.com/bar/baz.html', 'http://www.foo.com'),
    ('randoscheme://foo.com', 'randoscheme://foo.com'),
    ('foo', None),
    ('foo.com', None),
    ('http://www.foo.com/bar/baz.html?query=whatever', 'http://www.foo.com'),
    ('', None),
    (None, None)
])
def test_it_parses_scope_from_uri(uri, expected_scope):
    scope = scope_util.uri_scope(uri)

    assert scope == expected_scope


class TestScopeMatch(object):

    @pytest.mark.parametrize('uri,expected', [
        ('http://www.foo.com/bar/baz/ding.html', True),
        ('https://www.foo.com/bar/baz/ding.html', False),
        ('http://www.foo.com/', True),
        ('http://foo.com/bar.html', False),
        ('foo.com/bar.html', False)
    ])
    def test_it_matches_against_single_scope(self, uri, expected, single_scope):
        result = scope_util.match(uri, single_scope)

        assert result == expected

    @pytest.mark.parametrize('uri,expected', [
        ('http://www.foo.com/bar/baz/ding.html', True),
        ('http://www.bar.com/bar/baz/ding.html', True),
        ('http://www.foo.com/', True),
        ('http://www.bar.com', True),
        ('http://bar.com/bar.html', False),
        ('bar.com/bar.html', False)
    ])
    def test_it_matches_against_multiple_scopes(self, uri, expected, multiple_scopes):
        result = scope_util.match(uri, multiple_scopes)

        assert result == expected

    @pytest.fixture
    def single_scope(self):
        return ['http://www.foo.com']

    @pytest.fixture
    def multiple_scopes(self):
        return ['http://www.foo.com', 'http://www.bar.com']
