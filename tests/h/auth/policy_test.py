import base64
from unittest import mock
from unittest.mock import sentinel

import pytest
from h_matchers import Any
from pyramid.interfaces import IAuthenticationPolicy
from pyramid.security import Authenticated, Everyone

from h.auth.policy import (
    AUTH_CLIENT_API_WHITELIST,
    APIAuthenticationPolicy,
    AuthClientPolicy,
    AuthenticationPolicy,
    TokenAuthenticationPolicy,
)
from h.exceptions import InvalidUserId
from h.security import Identity

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


class TestAuthClientAuthenticationPolicy:
    def test_it_instantiates_a_BasicAuthAuthenticationPolicy(
        self, BasicAuthAuthenticationPolicy
    ):
        AuthClientPolicy()

        BasicAuthAuthenticationPolicy.assert_called_once_with(
            check=AuthClientPolicy.check
        )

    def test_unauthenticated_userid_returns_forwarded_user_if_present(
        self, auth_policy, pyramid_request
    ):
        pyramid_request.headers["X-Forwarded-User"] = "filbert"

        userid = auth_policy.unauthenticated_userid(pyramid_request)

        assert userid == "filbert"

    def test_unauthenticated_userid_returns_clientid_if_no_forwarded_user(
        self, auth_policy, pyramid_request, auth_client
    ):
        userid = auth_policy.unauthenticated_userid(pyramid_request)

        assert userid == auth_client.id

    def test_unauthenticated_userid_proxies_to_basic_auth_if_no_forwarded_user(
        self, pyramid_request, BasicAuthAuthenticationPolicy
    ):
        auth_policy = AuthClientPolicy()
        unauth_id = auth_policy.unauthenticated_userid(pyramid_request)

        BasicAuthAuthenticationPolicy.return_value.unauthenticated_userid.assert_called_once_with(
            pyramid_request
        )
        assert (
            unauth_id
            == BasicAuthAuthenticationPolicy.return_value.unauthenticated_userid.return_value
        )

    def test_unauthenticated_userid_doesnt_proxy_to_basic_auth_if_forwarded_user(
        self, pyramid_request, BasicAuthAuthenticationPolicy
    ):
        pyramid_request.headers["X-Forwarded-User"] = "dingbat"
        auth_policy = AuthClientPolicy()

        auth_policy.unauthenticated_userid(pyramid_request)

        assert not (
            BasicAuthAuthenticationPolicy.return_value.unauthenticated_userid.call_count
        )

    def test_authenticated_userid_returns_None_if_no_forwarded_userid(
        self, auth_policy, pyramid_request
    ):
        userid = auth_policy.authenticated_userid(pyramid_request)

        assert userid is None

    def test_authenticated_userid_proxies_to_basic_auth_policy_if_forwarded_user(
        self, pyramid_request, BasicAuthAuthenticationPolicy
    ):
        pyramid_request.headers["X-Forwarded-User"] = "dingbat"
        auth_policy = AuthClientPolicy()
        auth_policy.authenticated_userid(pyramid_request)

        BasicAuthAuthenticationPolicy.return_value.unauthenticated_userid.assert_called_once_with(
            pyramid_request
        )
        BasicAuthAuthenticationPolicy.return_value.callback.assert_called_once_with(
            BasicAuthAuthenticationPolicy.return_value.unauthenticated_userid.return_value,
            pyramid_request,
        )

    def test_authenticated_userid_does_not_proxy_if_no_forwarded_user(
        self, pyramid_request, BasicAuthAuthenticationPolicy
    ):
        auth_policy = AuthClientPolicy()
        auth_policy.authenticated_userid(pyramid_request)

        assert not (
            BasicAuthAuthenticationPolicy.return_value.unauthenticated_userid.call_count
        )
        assert not BasicAuthAuthenticationPolicy.return_value.callback.call_count

    def test_authenticated_userid_returns_userid_if_callback_ok(
        self, auth_policy, pyramid_request
    ):
        # check callback is mocked to return [], which is "OK"
        pyramid_request.headers["X-Forwarded-User"] = "dingbat"

        userid = auth_policy.authenticated_userid(pyramid_request)

        assert userid == "dingbat"

    def test_authenticated_userid_returns_None_if_callback_not_OK(
        self, check, pyramid_request
    ):
        check.return_value = None
        policy = AuthClientPolicy(check=check)

        pyramid_request.headers["X-Forwarded-User"] = "dingbat"

        userid = policy.authenticated_userid(pyramid_request)

        assert userid is None

    def test_effective_principals_proxies_to_basic_auth(
        self, pyramid_request, check, BasicAuthAuthenticationPolicy
    ):
        auth_policy = AuthClientPolicy()
        auth_policy.effective_principals(pyramid_request)

        BasicAuthAuthenticationPolicy.return_value.effective_principals.assert_called_once_with(
            pyramid_request
        )

    def test_effective_principals_returns_list_containing_callback_return_value(
        self, pyramid_request, check
    ):
        check.return_value = ["foople", "blueberry"]
        policy = AuthClientPolicy(check=check)

        principals = policy.effective_principals(pyramid_request)

        assert "foople" in principals
        assert "blueberry" in principals

    def test_effective_principals_returns_only_Everyone_if_callback_returns_None(
        self, pyramid_request, check
    ):
        check.return_value = None
        policy = AuthClientPolicy(check=check)

        principals = policy.effective_principals(pyramid_request)

        assert principals == ["system.Everyone"]

    def test_forget_does_nothing(self, auth_policy, pyramid_request):
        assert auth_policy.forget(pyramid_request) == []

    def test_remember_does_nothing(self, auth_policy, pyramid_request):
        assert auth_policy.remember(pyramid_request, "whoever") == []

    def test_check(
        self, pyramid_request, verify_auth_client, user_service, principals_for_identity
    ):
        pyramid_request.headers["X-Forwarded-User"] = sentinel.forwarded_user

        results = AuthClientPolicy.check(
            sentinel.username, sentinel.password, pyramid_request
        )

        verify_auth_client.assert_called_once_with(
            client_id=sentinel.username,
            client_secret=sentinel.password,
            db_session=pyramid_request.db,
        )
        user_service.fetch.assert_called_once_with(sentinel.forwarded_user)
        principals_for_identity.assert_called_once_with(
            Any.instance_of(Identity).with_attrs(
                {
                    "auth_client": verify_auth_client.return_value,
                    "user": user_service.fetch.return_value,
                }
            )
        )
        assert results == principals_for_identity.return_value

    def test_check_with_no_forwarded_user(
        self, pyramid_request, principals_for_identity
    ):
        pyramid_request.headers["X-Forwarded-User"] = None

        AuthClientPolicy.check(sentinel.username, sentinel.password, pyramid_request)
        principals_for_identity.assert_called_once_with(
            Any.instance_of(Identity).with_attrs({"user": None})
        )

    def test_check_with_invalid_user(self, pyramid_request, user_service):
        pyramid_request.headers["X-Forwarded-User"] = sentinel.forwarded_user
        user_service.fetch.side_effect = InvalidUserId("someid")

        results = AuthClientPolicy.check(
            sentinel.username, sentinel.password, pyramid_request
        )

        assert results is None

    def test_check_returns_None_with_missing_user(self, pyramid_request, user_service):
        pyramid_request.headers["X-Forwarded-User"] = sentinel.forwarded_user
        user_service.fetch.return_value = None

        results = AuthClientPolicy.check(
            sentinel.username, sentinel.password, pyramid_request
        )

        assert results is None

    def test_check_returns_None_if_forwarded_user_authority_mismatch(
        self, pyramid_request, verify_auth_client, user_service, factories
    ):
        mismatched_user = factories.User(authority="two.com")
        verify_auth_client.return_value = factories.ConfidentialAuthClient(
            authority="one.com"
        )
        user_service.fetch.return_value = mismatched_user
        pyramid_request.headers["X-Forwarded-User"] = mismatched_user.userid

        principals = AuthClientPolicy.check(
            "someusername", "somepassword", pyramid_request
        )

        assert principals is None

    @pytest.fixture
    def principals_for_identity(self, patch):
        return patch("h.auth.policy.principals_for_identity")

    @pytest.fixture(autouse=True)
    def verify_auth_client(self, patch, user_service):
        verify_auth_client = patch("h.auth.util.verify_auth_client")
        # Ensure the auth client authority and user authority match by default
        verify_auth_client.return_value.authority = (
            user_service.fetch.return_value.authority
        )
        return verify_auth_client

    @pytest.fixture
    def check(self):
        check = mock.create_autospec(
            AuthClientPolicy.check, spec_set=True, instance=True
        )
        check.return_value = []
        return check

    @pytest.fixture
    def auth_client(self, factories):
        return factories.ConfidentialAuthClient(authority="one.com")

    @pytest.fixture
    def auth_policy(self, check):
        auth_policy = AuthClientPolicy(check=check)
        return auth_policy

    @pytest.fixture
    def pyramid_request(self, pyramid_request, auth_client):
        user_pass = "{client_id}:{client_secret}".format(
            client_id=auth_client.id, client_secret=auth_client.secret
        )
        encoded = base64.standard_b64encode(user_pass.encode("utf-8"))
        pyramid_request.headers["Authorization"] = "Basic {creds}".format(
            creds=encoded.decode("ascii")
        )
        return pyramid_request

    @pytest.fixture
    def BasicAuthAuthenticationPolicy(self, patch):
        return patch("h.auth.policy.BasicAuthAuthenticationPolicy")


@pytest.mark.usefixtures("user_service", "auth_token_service")
class TestTokenAuthenticationPolicy:
    def test_remember_does_nothing(self, pyramid_request):
        assert TokenAuthenticationPolicy().remember(pyramid_request, "foo") == []

    def test_forget_does_nothing(self, pyramid_request):
        assert TokenAuthenticationPolicy().forget(pyramid_request) == []

    def test_unauthenticated_userid_is_none_if_no_token(self, pyramid_request):
        assert (
            TokenAuthenticationPolicy().unauthenticated_userid(pyramid_request) is None
        )

    def test_identity(self, pyramid_request, auth_token_service, user_service):
        pyramid_request.auth_token = sentinel.auth_token

        identity = TokenAuthenticationPolicy().identity(pyramid_request)

        auth_token_service.validate.assert_called_once_with(sentinel.auth_token)
        user_service.fetch.assert_called_once_with(
            auth_token_service.validate.return_value.userid
        )
        assert identity == Identity(user=user_service.fetch.return_value)

    def test_identify_for_webservice(self, pyramid_request, auth_token_service):
        pyramid_request.auth_token = sentinel.decoy
        pyramid_request.path = "/ws"
        pyramid_request.GET["access_token"] = sentinel.access_token

        TokenAuthenticationPolicy().identity(pyramid_request)

        auth_token_service.validate.assert_called_once_with(sentinel.access_token)

    def test_identity_returns_None_with_no_token(self, pyramid_request):
        pyramid_request.auth_token = None

        assert TokenAuthenticationPolicy().identity(pyramid_request) is None

    def test_identity_returns_None_for_invalid_tokens(
        self, pyramid_request, auth_token_service
    ):
        pyramid_request.auth_token = sentinel.auth_token
        auth_token_service.validate.return_value = None

        assert TokenAuthenticationPolicy().identity(pyramid_request) is None

    def test_identity_returns_None_for_invalid_users(
        self, pyramid_request, user_service
    ):
        pyramid_request.auth_token = sentinel.auth_token
        user_service.fetch.return_value = None

        assert TokenAuthenticationPolicy().identity(pyramid_request) is None

    @pytest.mark.parametrize(
        "method", ("unauthenticated_userid", "authenticated_userid")
    )
    def test_userid_method(self, pyramid_request, user_service, method):
        pyramid_request.auth_token = sentinel.auth_token

        result = getattr(TokenAuthenticationPolicy(), method)(pyramid_request)

        assert result == user_service.fetch.return_value.userid

    @pytest.mark.parametrize(
        "method", ("unauthenticated_userid", "authenticated_userid")
    )
    def test_userid_method_returns_None_with_no_identity(self, pyramid_request, method):
        pyramid_request.auth_token = None

        assert getattr(TokenAuthenticationPolicy(), method)(pyramid_request) is None

    def test_authenticated_userid_returns_None_with_no_user(
        self,
        pyramid_request,
    ):
        pyramid_request.auth_token = None

        assert (
            TokenAuthenticationPolicy().unauthenticated_userid(pyramid_request) is None
        )

    def test_effective_principals(
        self, pyramid_request, user_service, principals_for_identity
    ):
        principals_for_identity.return_value = ["principal"]
        pyramid_request.auth_token = sentinel.auth_token

        result = TokenAuthenticationPolicy().effective_principals(pyramid_request)

        assert result == [
            Everyone,
            Authenticated,
            user_service.fetch.return_value.userid,
            "principal",
        ]

    def test_effective_principals_with_no_identity(self, pyramid_request):
        pyramid_request.auth_token = None

        result = TokenAuthenticationPolicy().effective_principals(pyramid_request)

        assert result == [Everyone]

    @pytest.fixture(autouse=True)
    def principals_for_identity(self, patch):
        return patch("h.auth.policy.principals_for_identity")
