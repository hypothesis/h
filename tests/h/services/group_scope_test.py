# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import mock

from h.services.group_scope import group_scope_factory, GroupScopeService


class TestFetchByOrigin(object):
    def test_it_proxies_to_scope_util_for_origin_parsing(
        self, svc, scope_util, document_uri
    ):
        scope_util.parse_origin.return_value = "parsed"
        svc.fetch_by_origin(document_uri)

        scope_util.parse_origin.assert_called_once_with(document_uri)

    def test_it_returns_empty_list_if_origin_not_parseable(
        self, svc, scope_util, document_uri
    ):
        scope_util.parse_origin.return_value = None
        scopes = svc.fetch_by_origin(document_uri)

        assert scopes == []

    @pytest.mark.parametrize(
        "uri,should_match",
        [
            ("https://www.foo.com", False),
            ("http://foo.com", True),
            ("https://foo.com/bar", False),
            ("http://foo.com/bar/baz/", True),
            ("http://www.foo.com/bar/baz.html", False),
            ("randoscheme://foo.com", False),
            ("foo", False),
            ("foo.com", False),
            ("http://foo.com/bar/baz.html?query=whatever", True),
            ("", False),
            (None, False),
        ],
    )
    def test_it_returns_scopes_that_match_uri_origin(
        self, svc, sample_scopes, uri, should_match
    ):
        matches = svc.fetch_by_origin(uri)

        if should_match:
            assert matches == sample_scopes
        else:
            assert matches == []


class TestFetchByScope(object):
    def test_it_proxies_to_fetch_by_origin(self, svc, document_uri):
        svc.fetch_by_origin = mock.Mock(return_value=[])

        svc.fetch_by_scope(document_uri)

        svc.fetch_by_origin.assert_called_once_with(document_uri)

    def test_it_returns_list_of_matching_scopes(self, svc, document_uri, sample_scopes):
        results = svc.fetch_by_scope(document_uri)

        matching_scope_scopes = [scope.scope for scope in results]
        assert len(results) == 2
        assert "http://foo.com" in matching_scope_scopes
        assert "http://foo.com/bar/" in matching_scope_scopes


class TestGroupScopeFactory(object):
    def test_it_returns_group_scope_service_instance(self, pyramid_request):
        svc = group_scope_factory(None, pyramid_request)

        assert isinstance(svc, GroupScopeService)


@pytest.fixture
def svc(db_session, pyramid_request):
    pyramid_request.db = db_session
    return group_scope_factory({}, pyramid_request)


@pytest.fixture
def scope_util(patch):
    return patch("h.services.group_scope.scope_util")


@pytest.fixture
def document_uri():
    return "http://foo.com/bar/foo.html"


@pytest.fixture
def sample_scopes(factories):
    return [
        factories.GroupScope(scope="http://foo.com"),
        factories.GroupScope(scope="http://foo.com/bar/"),
        factories.GroupScope(scope="http://foo.com/bar/baz/"),
        factories.GroupScope(
            scope="http://foo.com/bar/baz/foo.html?q=something&wut=how"
        ),
    ]
