import pytest

from h.services.group_scope import GroupScopeService, group_scope_factory


class TestFetchByScope:
    def test_it_returns_empty_list_if_origin_not_parseable(
        self, svc, scope_util, document_uri
    ):
        scope_util.parse_origin.return_value = None
        scopes = svc.fetch_by_scope(document_uri)

        assert scopes == []

    def test_it_only_returns_scopes_that_pass_util_scope_test(
        self, svc, scope_util, sample_scopes
    ):
        scope_util.url_in_scope.return_value = False
        scope_util.parse_origin.return_value = "http://foo.com"

        # All sample_scopes match this URL, but fail the `url_in_scope` test
        scopes = svc.fetch_by_scope("http://foo.com")

        assert scope_util.url_in_scope.call_count == len(sample_scopes)
        assert scopes == []

    @pytest.mark.usefixtures("sample_scopes")
    def test_it_returns_list_of_matching_scopes(self, svc, document_uri):
        results = svc.fetch_by_scope(document_uri)

        matching_scope_scopes = [scope.scope for scope in results]
        assert len(results) == 2
        assert "http://foo.com" in matching_scope_scopes
        assert "http://foo.com/bar/" in matching_scope_scopes


class TestGroupScopeFactory:
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
