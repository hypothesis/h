import base64
from unittest import mock
from unittest.mock import sentinel

import pytest
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
from h.models.auth_client import GrantType
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
class TestAuthClientPolicy:
    def test_identity(self, pyramid_request, auth_client, user_service):
        pyramid_request.headers["X-Forwarded-User"] = sentinel.forwarded_user

        identity = AuthClientPolicy().identity(pyramid_request)

        user_service.fetch.assert_called_once_with(sentinel.forwarded_user)
        assert identity == Identity(
            auth_client=auth_client, user=user_service.fetch.return_value
        )

    def test_identify_without_forwarded_user(self, pyramid_request, auth_client):
        pyramid_request.headers["X-Forwarded-User"] = None

        identity = AuthClientPolicy().identity(pyramid_request)

        assert identity == Identity(auth_client=auth_client)

    def test_identity_returns_None_without_credentials(self, pyramid_request):
        pyramid_request.headers["Authorization"] = None

        assert AuthClientPolicy().identity(pyramid_request) is None

    def test_identity_returns_None_if_auth_client_id_is_invalid(
        self, pyramid_request, auth_client, db_session
    ):
        db_session.delete(auth_client)
        db_session.flush()

        assert AuthClientPolicy().identity(pyramid_request) is None

    def test_identity_returns_None_if_auth_client_missing(
        self, pyramid_request, auth_client, db_session
    ):
        db_session.delete(auth_client)
        db_session.flush()

        assert AuthClientPolicy().identity(pyramid_request) is None

    def test_identify_returns_None_if_auth_client_not_secret(
        self, auth_client, pyramid_request
    ):
        self.set_http_credentials(pyramid_request, "NOT A UUID", auth_client.secret)

        assert AuthClientPolicy().identity(pyramid_request) is None

    def test_identify_returns_None_if_auth_client_not_client_type(
        self, auth_client, pyramid_request
    ):
        auth_client.grant_type = None

        assert AuthClientPolicy().identity(pyramid_request) is None

    def test_identify_returns_None_if_auth_client_secret_is_None(
        self, auth_client, pyramid_request
    ):
        auth_client.secret = None

        assert AuthClientPolicy().identity(pyramid_request) is None

    def test_identify_returns_None_if_auth_client_secrets_do_not_match(
        self, auth_client, pyramid_request
    ):
        self.set_http_credentials(pyramid_request, auth_client.id, "WRONG SECRET")

        assert AuthClientPolicy().identity(pyramid_request) is None

    def test_identify_returns_None_if_forwarded_user_is_not_found(
        self, user_service, pyramid_request
    ):
        user_service.fetch.return_value = None

        assert AuthClientPolicy().identity(pyramid_request) is None

    def test_identify_returns_None_if_forwarded_userid_is_invalid(
        self, user_service, pyramid_request
    ):
        user_service.fetch.side_effect = InvalidUserId(sentinel.invalid_id)

        assert AuthClientPolicy().identity(pyramid_request) is None

    def test_identify_returns_None_on_forwarded_userid_authority_mismatch(
        self, user, auth_client, pyramid_request
    ):
        user.authority = "not" + auth_client.authority

        assert AuthClientPolicy().identity(pyramid_request) is None

    def test_unauthenticated_userid(self, pyramid_request):
        pyramid_request.headers["X-Forwarded-User"] = "forwarded-user"

        assert (
            AuthClientPolicy().unauthenticated_userid(pyramid_request)
            == "forwarded-user"
        )

    def test_unauthenticated_userid_returns_clientid_if_no_forwarded_user(
        self, pyramid_request, auth_client
    ):
        pyramid_request.headers["X-Forwarded-User"] = None

        assert (
            AuthClientPolicy().unauthenticated_userid(pyramid_request) == auth_client.id
        )

    def test_unauthenticated_userid_returns_None_if_no_credentials(
        self, pyramid_request, auth_client
    ):
        pyramid_request.headers["Authorization"] = None
        pyramid_request.headers["X-Forwarded-User"] = None

        assert AuthClientPolicy().unauthenticated_userid(pyramid_request) is None

    @pytest.fixture
    def auth_client(self, factories):
        return factories.ConfidentialAuthClient(grant_type=GrantType.client_credentials)

    @pytest.fixture(autouse=True)
    def with_credentials(self, pyramid_request, auth_client):
        self.set_http_credentials(pyramid_request, auth_client.id, auth_client.secret)
        pyramid_request.headers["X-Forwarded-User"] = sentinel.forwarded_user

    @classmethod
    def set_http_credentials(cls, pyramid_request, client_id, client_secret):
        encoded = base64.standard_b64encode(
            f"{client_id}:{client_secret}".encode("utf-8")
        )
        creds = encoded.decode("ascii")
        pyramid_request.headers["Authorization"] = f"Basic {creds}"

    @pytest.fixture(autouse=True)
    def user(self, factories, auth_client, user_service):
        user = factories.User(authority=auth_client.authority)
        user_service.fetch.return_value = user
        return user


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

    @pytest.mark.parametrize("with_auth_client", (True, False))
    def test_effective_principals(
        self,
        policy,
        pyramid_request,
        identity,
        principals_for_identity,
        with_auth_client,
        factories,
    ):
        if with_auth_client:
            identity.auth_client = factories.AuthClient()

        principals_for_identity.return_value = ["principal"]

        principals = policy.effective_principals(pyramid_request)

        principals_for_identity.assert_called_once_with(identity)
        assert principals == [
            Everyone,
            Authenticated,
            # I'm suspicious that this is an either or. I feel like both values
            # should just be dependant on the presence of the relevant thing
            identity.auth_client.id if with_auth_client else identity.user.userid,
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
