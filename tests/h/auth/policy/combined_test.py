from unittest import mock

import pytest
from pyramid.interfaces import IAuthenticationPolicy
from pyramid.security import Authenticated, Everyone

from h.auth.policy._basic_http_auth import AuthClientPolicy
from h.auth.policy.bearer_token import TokenAuthenticationPolicy
from h.auth.policy.combined import (
    AUTH_CLIENT_API_WHITELIST,
    APIAuthenticationPolicy,
    AuthenticationPolicy,
)

API_PATHS = ("/api", "/api/foo", "/api/annotations/abc123")

NONAPI_PATHS = ("/login", "/account/settings", "/api/badge", "/api/token")

AUTH_CLIENT_API_BLACKLIST = [
    ("api.groups", "GET"),
    ("api.user", "POST"),
    ("group_create", "POST"),
    ("api.group_member", "DELETE"),
]


class TestAuthenticationPolicy:
    @pytest.fixture(autouse=True)
    def policy(self):
        # pylint:disable=attribute-defined-outside-init
        self.api_policy = mock.Mock(spec_set=list(IAuthenticationPolicy))
        self.fallback_policy = mock.Mock(spec_set=list(IAuthenticationPolicy))
        self.policy = AuthenticationPolicy(
            api_policy=self.api_policy, fallback_policy=self.fallback_policy
        )

        self.fallback_policy.remember.return_value = [("Cookie", "auth=foobar")]

    # api_request and nonapi_request are parametrized fixtures, which will
    # take on each value in the passed `params` sequence in turn. This is a
    # quick and easy way to generate a named fixture which takes multiple
    # values and can be used by multiple tests.
    @pytest.fixture(params=API_PATHS)
    def api_request(self, request, pyramid_request):
        pyramid_request.path = request.param
        return pyramid_request

    @pytest.fixture(params=NONAPI_PATHS)
    def nonapi_request(self, request, pyramid_request):
        pyramid_request.path = request.param
        return pyramid_request

    def test_authenticated_userid_uses_fallback_policy_for_nonapi_paths(
        self, nonapi_request
    ):
        result = self.policy.authenticated_userid(nonapi_request)

        self.fallback_policy.authenticated_userid.assert_called_once_with(
            nonapi_request
        )
        assert result == self.fallback_policy.authenticated_userid.return_value

    def test_authenticated_userid_uses_api_policy_for_api_paths(self, api_request):
        result = self.policy.authenticated_userid(api_request)

        self.api_policy.authenticated_userid.assert_called_once_with(api_request)
        assert result == self.api_policy.authenticated_userid.return_value

    def test_unauthenticated_userid_uses_fallback_policy_for_nonapi_paths(
        self, nonapi_request
    ):
        result = self.policy.unauthenticated_userid(nonapi_request)

        self.fallback_policy.unauthenticated_userid.assert_called_once_with(
            nonapi_request
        )
        assert result == self.fallback_policy.unauthenticated_userid.return_value

    def test_unauthenticated_userid_uses_api_policy_for_api_paths(self, api_request):
        result = self.policy.unauthenticated_userid(api_request)

        self.api_policy.unauthenticated_userid.assert_called_once_with(api_request)
        assert result == self.api_policy.unauthenticated_userid.return_value

    def test_effective_principals_uses_fallback_policy_for_nonapi_paths(
        self, nonapi_request
    ):
        result = self.policy.effective_principals(nonapi_request)

        self.fallback_policy.effective_principals.assert_called_once_with(
            nonapi_request
        )
        assert result == self.fallback_policy.effective_principals.return_value

    def test_effective_principals_uses_api_policy_for_api_paths(self, api_request):
        result = self.policy.effective_principals(api_request)

        self.api_policy.effective_principals.assert_called_once_with(api_request)
        assert result == self.api_policy.effective_principals.return_value

    def test_remember_uses_fallback_policy_for_nonapi_paths(self, nonapi_request):
        result = self.policy.remember(nonapi_request, "foo", bar="baz")

        self.fallback_policy.remember.assert_called_once_with(
            nonapi_request, "foo", bar="baz"
        )
        assert result == self.fallback_policy.remember.return_value

    def test_remember_uses_api_policy_for_api_paths(self, api_request):
        result = self.policy.remember(api_request, "foo", bar="baz")

        self.api_policy.remember.assert_called_once_with(api_request, "foo", bar="baz")
        assert result == self.api_policy.remember.return_value

    def test_forget_uses_fallback_policy_for_nonapi_paths(self, nonapi_request):
        result = self.policy.forget(nonapi_request)

        self.fallback_policy.forget.assert_called_once_with(nonapi_request)
        assert result == self.fallback_policy.forget.return_value

    def test_forget_uses_api_policy_for_api_paths(self, api_request):
        result = self.policy.forget(api_request)

        self.api_policy.forget.assert_called_once_with(api_request)
        assert result == self.api_policy.forget.return_value


class TestAPIAuthenticationPolicy:
    def test_authenticated_userid_proxies_to_user_policy_first(
        self, pyramid_request, api_policy, user_policy, client_policy
    ):
        userid = api_policy.authenticated_userid(pyramid_request)

        user_policy.authenticated_userid.assert_called_once_with(pyramid_request)
        assert not client_policy.authenticated_userid.call_count
        assert userid == user_policy.authenticated_userid.return_value

    @pytest.mark.parametrize("route_name,route_method", AUTH_CLIENT_API_WHITELIST)
    def test_authenticated_userid_proxies_to_client_policy_if_user_fails(
        self,
        pyramid_request,
        api_policy,
        user_policy,
        client_policy,
        route_name,
        route_method,
    ):
        pyramid_request.method = route_method
        pyramid_request.matched_route.name = route_name
        user_policy.authenticated_userid.return_value = None

        userid = api_policy.authenticated_userid(pyramid_request)

        user_policy.authenticated_userid.assert_called_once_with(pyramid_request)
        client_policy.authenticated_userid.assert_called_once_with(pyramid_request)
        assert userid == client_policy.authenticated_userid.return_value

    @pytest.mark.parametrize("route_name,route_method", AUTH_CLIENT_API_BLACKLIST)
    def test_authenticated_userid_does_not_proxy_to_client_policy_if_path_mismatch(
        self,
        pyramid_request,
        api_policy,
        user_policy,
        client_policy,
        route_name,
        route_method,
    ):
        pyramid_request.method = route_method
        pyramid_request.matched_route.name = route_name
        user_policy.authenticated_userid.return_value = None

        userid = api_policy.authenticated_userid(pyramid_request)

        user_policy.authenticated_userid.assert_called_once_with(pyramid_request)
        assert not client_policy.authenticated_userid.call_count
        assert userid == user_policy.authenticated_userid.return_value

    @pytest.mark.parametrize("route_name,route_method", AUTH_CLIENT_API_WHITELIST)
    def test_unauthenticated_userid_proxies_to_user_policy_first(
        self,
        pyramid_request,
        api_policy,
        user_policy,
        client_policy,
        route_name,
        route_method,
    ):
        pyramid_request.method = route_method
        pyramid_request.matched_route.name = route_name
        userid = api_policy.unauthenticated_userid(pyramid_request)

        user_policy.unauthenticated_userid.assert_called_once_with(pyramid_request)
        assert not client_policy.unauthenticated_userid.call_count
        assert userid == user_policy.unauthenticated_userid.return_value

    def test_unauthenticated_userid_proxies_to_client_policy_if_user_fails(
        self, pyramid_request, api_policy, user_policy, client_policy
    ):
        user_policy.unauthenticated_userid.return_value = None

        userid = api_policy.unauthenticated_userid(pyramid_request)

        user_policy.unauthenticated_userid.assert_called_once_with(pyramid_request)
        client_policy.unauthenticated_userid.assert_called_once_with(pyramid_request)
        assert userid == client_policy.unauthenticated_userid.return_value

    @pytest.mark.parametrize("route_name,route_method", AUTH_CLIENT_API_BLACKLIST)
    def test_unauthenticated_userid_does_not_proxy_to_client_policy_if_path_mismatch(
        self,
        pyramid_request,
        api_policy,
        user_policy,
        client_policy,
        route_name,
        route_method,
    ):
        pyramid_request.method = route_method
        pyramid_request.matched_route.name = route_name
        user_policy.unauthenticated_userid.return_value = None

        userid = api_policy.unauthenticated_userid(pyramid_request)

        user_policy.unauthenticated_userid.assert_called_once_with(pyramid_request)
        assert not client_policy.unauthenticated_userid.call_count
        assert userid == user_policy.unauthenticated_userid.return_value

    def test_effective_principals_proxies_to_user_policy_first(
        self, pyramid_request, api_policy, user_policy, client_policy
    ):
        user_policy.effective_principals.return_value = [Everyone, Authenticated]

        principals = api_policy.effective_principals(pyramid_request)

        user_policy.effective_principals.assert_called_once_with(pyramid_request)
        assert not client_policy.effective_principals.call_count
        assert principals == user_policy.effective_principals.return_value

    @pytest.mark.parametrize("route_name,route_method", AUTH_CLIENT_API_WHITELIST)
    def test_effective_principals_proxies_to_client_if_auth_principal_missing(
        self,
        pyramid_request,
        api_policy,
        user_policy,
        client_policy,
        route_name,
        route_method,
    ):
        pyramid_request.method = route_method
        pyramid_request.matched_route.name = route_name
        user_policy.effective_principals.return_value = [Everyone]

        principals = api_policy.effective_principals(pyramid_request)

        user_policy.effective_principals.assert_called_once_with(pyramid_request)
        client_policy.effective_principals.assert_called_once_with(pyramid_request)
        assert principals == client_policy.effective_principals.return_value

    @pytest.mark.parametrize("route_name,route_method", AUTH_CLIENT_API_BLACKLIST)
    def test_effective_principals_does_not_proxy_to_client_if_path_mismatch(
        self,
        pyramid_request,
        api_policy,
        user_policy,
        client_policy,
        route_name,
        route_method,
    ):
        pyramid_request.method = route_method
        pyramid_request.matched_route.name = route_name
        user_policy.effective_principals.return_value = [Everyone]

        principals = api_policy.effective_principals(pyramid_request)

        user_policy.effective_principals.assert_called_once_with(pyramid_request)
        assert not client_policy.effective_principals.call_count
        assert principals == user_policy.effective_principals.return_value

    @pytest.mark.parametrize("route_name,route_method", AUTH_CLIENT_API_WHITELIST)
    def test_remember_proxies_to_user_policy_first(
        self, pyramid_request, api_policy, user_policy, route_name, route_method
    ):
        pyramid_request.method = route_method
        pyramid_request.matched_route.name = route_name
        remembered = api_policy.remember(pyramid_request, "acct:foo@bar.com")

        user_policy.remember.assert_called_once_with(
            pyramid_request, "acct:foo@bar.com"
        )
        assert remembered == user_policy.remember.return_value

    def test_remember_proxies_to_client_policy_second(
        self, pyramid_request, api_policy, user_policy, client_policy
    ):
        user_policy.remember.return_value = []

        remembered = api_policy.remember(pyramid_request, "acct:foo@bar.com")

        user_policy.remember.assert_called_once_with(
            pyramid_request, "acct:foo@bar.com"
        )
        client_policy.remember.assert_called_once_with(
            pyramid_request, "acct:foo@bar.com"
        )
        assert remembered == client_policy.remember.return_value

    @pytest.mark.parametrize("route_name,route_method", AUTH_CLIENT_API_BLACKLIST)
    def test_remember_does_not_proxy_to_client_if_path_mismatch(
        self,
        pyramid_request,
        api_policy,
        user_policy,
        client_policy,
        route_name,
        route_method,
    ):
        pyramid_request.method = route_method
        pyramid_request.matched_route.name = route_name
        user_policy.remember.return_value = []

        remembered = api_policy.remember(pyramid_request, "acct:foo@bar.com")

        user_policy.remember.assert_called_once_with(
            pyramid_request, "acct:foo@bar.com"
        )
        assert not client_policy.remember.call_count
        assert remembered == user_policy.remember.return_value

    @pytest.mark.parametrize("route_name,route_method", AUTH_CLIENT_API_WHITELIST)
    def test_forget_proxies_to_user_policy_first(
        self, pyramid_request, api_policy, user_policy, route_name, route_method
    ):
        pyramid_request.method = route_method
        pyramid_request.matched_route.name = route_name
        forgot = api_policy.forget(pyramid_request)

        user_policy.forget.assert_called_once_with(pyramid_request)
        assert forgot == user_policy.forget.return_value

    def test_forget_proxies_to_client_policy_second(
        self, pyramid_request, api_policy, user_policy, client_policy
    ):
        user_policy.forget.return_value = []

        forgot = api_policy.forget(pyramid_request)

        user_policy.forget.assert_called_once_with(pyramid_request)
        client_policy.forget.assert_called_once_with(pyramid_request)
        assert forgot == client_policy.forget.return_value

    @pytest.mark.parametrize("route_name,route_method", AUTH_CLIENT_API_BLACKLIST)
    def test_forget_does_not_proxy_to_client_if_path_mismatch(
        self,
        pyramid_request,
        api_policy,
        user_policy,
        client_policy,
        route_name,
        route_method,
    ):
        pyramid_request.method = route_method
        pyramid_request.matched_route.name = route_name
        user_policy.forget.return_value = []

        forgot = api_policy.forget(pyramid_request)

        user_policy.forget.assert_called_once_with(pyramid_request)
        assert not client_policy.forget.call_count
        assert forgot == user_policy.forget.return_value

    def test_forget_does_not_proxy_with_no_matched_route(
        self, pyramid_request, api_policy, user_policy, client_policy
    ):
        pyramid_request.matched_route = None
        user_policy.forget.return_value = []

        forgot = api_policy.forget(pyramid_request)
        assert not client_policy.forget.call_count
        assert forgot == user_policy.forget.return_value

    @pytest.fixture
    def client_policy(self):
        return mock.create_autospec(AuthClientPolicy, instance=True, spec_set=True)

    @pytest.fixture
    def user_policy(self):
        return mock.create_autospec(
            TokenAuthenticationPolicy, instance=True, spec_set=True
        )

    @pytest.fixture
    def api_policy(self, client_policy, user_policy):
        return APIAuthenticationPolicy(
            user_policy=user_policy, client_policy=client_policy
        )

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.matched_route.name = "api.groups"
        pyramid_request.method = "POST"
        return pyramid_request
