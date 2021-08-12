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
    IdentityBasedPolicy,
    RemoteUserAuthenticationPolicy,
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


@pytest.mark.usefixtures("user_service")
class TestAuthClientAuthenticationPolicy:
    def test_unauthenticated_userid(self, pyramid_request):
        pyramid_request.headers["X-Forwarded-User"] = "forwarded-user"

        userid = AuthClientPolicy().unauthenticated_userid(pyramid_request)

        assert userid == "forwarded-user"

    @pytest.mark.usefixtures("with_auth_client_credentials")
    def test_unauthenticated_userid_returns_clientid_if_no_forwarded_user(
        self, pyramid_request, auth_client
    ):
        userid = AuthClientPolicy().unauthenticated_userid(pyramid_request)

        assert userid == auth_client.id

    @pytest.mark.usefixtures("with_auth_client_credentials")
    def test_authenticated_userid(self, pyramid_request):
        pyramid_request.headers["X-Forwarded-User"] = "forwarded-user"

        userid = AuthClientPolicy().unauthenticated_userid(pyramid_request)

        assert userid == "forwarded-user"

    @pytest.mark.usefixtures("with_auth_client_credentials")
    def test_authenticated_userid_returns_None_with_no_forwarded_user(
        self, pyramid_request
    ):
        pyramid_request.headers["X-Forwarded-User"] = None

        userid = AuthClientPolicy().authenticated_userid(pyramid_request)

        assert userid is None

    @pytest.mark.usefixtures("with_auth_client_credentials")
    def test_effective_principals(
        self, pyramid_request, principals_for_identity, auth_client
    ):
        pyramid_request.headers["X-Forwarded-User"] = "forwarded-user"
        principals_for_identity.return_value = ["principal"]

        principals = AuthClientPolicy().effective_principals(pyramid_request)

        expected_principals = [
            Everyone,
            Authenticated,
            "principal",
            # Is this intended or useful behavior? Or just what we got from
            # the base policy?
            auth_client.id,
        ]
        assert principals == Any.list.containing(expected_principals).only()

    @pytest.mark.usefixtures("with_auth_client_credentials")
    def test_effective_principals_when_check_returns_None(
        self, pyramid_request, principals_for_identity, auth_client
    ):
        pyramid_request.headers["X-Forwarded-User"] = "forwarded-user"
        principals_for_identity.return_value = None

        principals = AuthClientPolicy().effective_principals(pyramid_request)

        assert principals == [Everyone]

    def test_forget_does_nothing(self, pyramid_request):
        assert AuthClientPolicy().forget(pyramid_request) == []

    def test_remember_does_nothing(self, pyramid_request):
        assert AuthClientPolicy().remember(pyramid_request, "whoever") == []

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
    def auth_client(self, factories):
        return factories.ConfidentialAuthClient(authority="one.com")

    @pytest.fixture
    def with_auth_client_credentials(self, pyramid_request, auth_client):
        user_pass = "{client_id}:{client_secret}".format(
            client_id=auth_client.id, client_secret=auth_client.secret
        )
        encoded = base64.standard_b64encode(user_pass.encode("utf-8"))
        pyramid_request.headers["Authorization"] = "Basic {creds}".format(
            creds=encoded.decode("ascii")
        )


class TestIdentityBasedPolicy:
    def test_identity_method_does_nothing(self, pyramid_request):
        assert IdentityBasedPolicy().identity(pyramid_request) is None

    @pytest.mark.parametrize(
        "method", ("authenticated_userid", "unauthenticated_userid")
    )
    def test_userid_methods(self, policy, pyramid_request, identity, method):
        assert getattr(policy, method)(pyramid_request) == identity.user.userid

    @pytest.mark.parametrize(
        "method", ("authenticated_userid", "unauthenticated_userid")
    )
    def test_userid_methods_return_None_if_the_identity_has_no_user(
        self, policy, pyramid_request, identity, method
    ):
        identity.user = None

        assert getattr(policy, method)(pyramid_request) is None

    @pytest.mark.parametrize(
        "method", ("authenticated_userid", "unauthenticated_userid")
    )
    def test_userid_methods_return_None_if_the_identity_is_None(
        self, policy, pyramid_request, method
    ):
        policy.returned_identity = None

        assert getattr(policy, method)(pyramid_request) is None

    def test_effective_principals(
        self, policy, pyramid_request, identity, principals_for_identity
    ):
        principals_for_identity.return_value = ["principal"]

        principals = policy.effective_principals(pyramid_request)

        principals_for_identity.assert_called_once_with(identity)
        assert principals == [
            Everyone,
            Authenticated,
            identity.user.userid,
            "principal",
        ]

    def test_effective_principals_with_no_identity(self, policy, pyramid_request):
        policy.returned_identity = None

        assert policy.effective_principals(pyramid_request) == [Everyone]

    def test_remember_does_nothing(self, policy, pyramid_request):
        assert policy.remember(pyramid_request, "foo") == []

    def test_forget_does_nothing(self, policy, pyramid_request):
        assert policy.forget(pyramid_request) == []

    @pytest.fixture
    def identity(self, factories):
        return Identity(user=factories.User())

    @pytest.fixture
    def policy(self, identity):
        class CustomPolicy(IdentityBasedPolicy):
            returned_identity = None

            def identity(self, _request):
                return self.returned_identity

        policy = CustomPolicy()
        policy.returned_identity = identity

        return policy

    @pytest.fixture(autouse=True)
    def principals_for_identity(self, patch):
        return patch("h.auth.policy.principals_for_identity")


@pytest.mark.usefixtures("user_service", "auth_token_service")
class TestTokenAuthenticationPolicy:
    def test_identity(self, pyramid_request, auth_token_service, user_service):
        pyramid_request.auth_token = sentinel.auth_token

        identity = TokenAuthenticationPolicy().identity(pyramid_request)

        auth_token_service.validate.assert_called_once_with(sentinel.auth_token)
        user_service.fetch.assert_called_once_with(
            auth_token_service.validate.return_value.userid
        )
        assert identity == Identity(user=user_service.fetch.return_value)

    def test_identity_for_webservice(self, pyramid_request, auth_token_service):
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


@pytest.mark.usefixtures("user_service")
class TestRemoteUserAuthenticationPolicy:
    def test_unauthenticated_userid(self, pyramid_request):
        pyramid_request.environ["HTTP_X_FORWARDED_USER"] = sentinel.forwarded_user

        userid = RemoteUserAuthenticationPolicy().unauthenticated_userid(
            pyramid_request
        )

        assert userid == sentinel.forwarded_user

    def test_identity(self, pyramid_request, user_service):
        pyramid_request.environ["HTTP_X_FORWARDED_USER"] = sentinel.forwarded_user

        identity = RemoteUserAuthenticationPolicy().identity(pyramid_request)

        user_service.fetch.assert_called_once_with(sentinel.forwarded_user)
        assert identity == Identity(user=user_service.fetch.return_value)

    def test_identity_returns_None_for_no_forwarded_user(self, pyramid_request):
        pyramid_request.environ["HTTP_X_FORWARDED_USER"] = None

        assert RemoteUserAuthenticationPolicy().identity(pyramid_request) is None

    def test_identity_returns_None_for_no_user(self, pyramid_request, user_service):
        pyramid_request.environ["HTTP_X_FORWARDED_USER"] = sentinel.forwarded_user
        user_service.fetch.return_value = None

        assert RemoteUserAuthenticationPolicy().identity(pyramid_request) is None
