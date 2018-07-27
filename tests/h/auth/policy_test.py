# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import mock
import pytest
import base64

from pyramid.interfaces import IAuthenticationPolicy

from h.auth.policy import AuthenticationPolicy
from h.auth.policy import TokenAuthenticationPolicy
from h.auth.policy import AuthClientPolicy

API_PATHS = (
    '/api',
    '/api/foo',
    '/api/annotations/abc123',
)

NONAPI_PATHS = (
    '/login',
    '/account/settings',
    '/api/badge',
    '/api/token',
)


class TestAuthenticationPolicy(object):

    @pytest.fixture(autouse=True)
    def policy(self):
        self.api_policy = mock.Mock(spec_set=list(IAuthenticationPolicy))
        self.fallback_policy = mock.Mock(spec_set=list(IAuthenticationPolicy))
        self.policy = AuthenticationPolicy(api_policy=self.api_policy,
                                           fallback_policy=self.fallback_policy)

        self.fallback_policy.remember.return_value = [('Cookie', 'auth=foobar')]

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

    def test_authenticated_userid_uses_fallback_policy_for_nonapi_paths(self, nonapi_request):
        result = self.policy.authenticated_userid(nonapi_request)

        self.fallback_policy.authenticated_userid.assert_called_once_with(nonapi_request)
        assert result == self.fallback_policy.authenticated_userid.return_value

    def test_authenticated_userid_uses_api_policy_for_api_paths(self, api_request):
        result = self.policy.authenticated_userid(api_request)

        self.api_policy.authenticated_userid.assert_called_once_with(api_request)
        assert result == self.api_policy.authenticated_userid.return_value

    def test_unauthenticated_userid_uses_fallback_policy_for_nonapi_paths(self, nonapi_request):
        result = self.policy.unauthenticated_userid(nonapi_request)

        self.fallback_policy.unauthenticated_userid.assert_called_once_with(nonapi_request)
        assert result == self.fallback_policy.unauthenticated_userid.return_value

    def test_unauthenticated_userid_uses_api_policy_for_api_paths(self, api_request):
        result = self.policy.unauthenticated_userid(api_request)

        self.api_policy.unauthenticated_userid.assert_called_once_with(api_request)
        assert result == self.api_policy.unauthenticated_userid.return_value

    def test_effective_principals_uses_fallback_policy_for_nonapi_paths(self, nonapi_request):
        result = self.policy.effective_principals(nonapi_request)

        self.fallback_policy.effective_principals.assert_called_once_with(nonapi_request)
        assert result == self.fallback_policy.effective_principals.return_value

    def test_effective_principals_uses_api_policy_for_api_paths(self, api_request):
        result = self.policy.effective_principals(api_request)

        self.api_policy.effective_principals.assert_called_once_with(api_request)
        assert result == self.api_policy.effective_principals.return_value

    def test_remember_uses_fallback_policy_for_nonapi_paths(self, nonapi_request):
        result = self.policy.remember(nonapi_request, 'foo', bar='baz')

        self.fallback_policy.remember.assert_called_once_with(nonapi_request, 'foo', bar='baz')
        assert result == self.fallback_policy.remember.return_value

    def test_remember_uses_api_policy_for_api_paths(self, api_request):
        result = self.policy.remember(api_request, 'foo', bar='baz')

        self.api_policy.remember.assert_called_once_with(api_request, 'foo', bar='baz')
        assert result == self.api_policy.remember.return_value

    def test_forget_uses_fallback_policy_for_nonapi_paths(self, nonapi_request):
        result = self.policy.forget(nonapi_request)

        self.fallback_policy.forget.assert_called_once_with(nonapi_request)
        assert result == self.fallback_policy.forget.return_value

    def test_forget_uses_api_policy_for_api_paths(self, api_request):
        result = self.policy.forget(api_request)

        self.api_policy.forget.assert_called_once_with(api_request)
        assert result == self.api_policy.forget.return_value


class TestAuthClientAuthenticationPolicy(object):

    def test_it_proxies_username_password_to_check_callback(self, pyramid_request, check):
        check.return_value = []
        policy = AuthClientPolicy(check=check)

        policy.effective_principals(pyramid_request)

        check.assert_called_once_with("foo", "bar", pyramid_request)

    def test_it_returns_None_for_authenticated_userid(self, pyramid_request, check):
        check.return_value = []
        policy = AuthClientPolicy(check=check)

        userid = policy.authenticated_userid(pyramid_request)

        assert userid is None

    def test_unauthenticated_userid_returns_client_id(self, pyramid_request, check):
        check.return_value = []
        policy = AuthClientPolicy(check=check)

        userid = policy.unauthenticated_userid(pyramid_request)

        assert userid == "foo"

    def test_remember_does_nothing(self, pyramid_request, check):
        policy = AuthClientPolicy(check=check)

        assert policy.remember(pyramid_request, 'foo') == []

    def test_forget_does_nothing(self, pyramid_request, check):
        policy = AuthClientPolicy(check=check)

        assert policy.forget(pyramid_request) == []

    @pytest.fixture
    def check(self):
        return mock.Mock()

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        user_pass = "foo:bar"
        encoded = base64.standard_b64encode(user_pass.encode('utf-8'))
        pyramid_request.headers['Authorization'] = "Basic {creds}".format(creds=encoded.decode('ascii'))
        return pyramid_request


@pytest.mark.usefixtures('token_service')
class TestTokenAuthenticationPolicy(object):
    def test_remember_does_nothing(self, pyramid_request):
        policy = TokenAuthenticationPolicy()

        assert policy.remember(pyramid_request, 'foo') == []

    def test_forget_does_nothing(self, pyramid_request):
        policy = TokenAuthenticationPolicy()

        assert policy.forget(pyramid_request) == []

    def test_unauthenticated_userid_is_none_if_no_token(self, pyramid_request):
        policy = TokenAuthenticationPolicy()

        assert policy.unauthenticated_userid(pyramid_request) is None

    def test_unauthenticated_userid_returns_userid_from_token(self, pyramid_request):
        policy = TokenAuthenticationPolicy()
        pyramid_request.auth_token = 'valid123'

        result = policy.unauthenticated_userid(pyramid_request)

        assert result == 'acct:foo@example.com'

    def test_unauthenticated_userid_returns_none_if_token_invalid(self, pyramid_request, token_service):
        policy = TokenAuthenticationPolicy()
        token_service.validate.return_value = None
        pyramid_request.auth_token = 'abcd123'

        result = policy.unauthenticated_userid(pyramid_request)

        assert result is None

    def test_unauthenticated_userid_returns_userid_from_query_params_token(self, pyramid_request):
        """When the path is `/ws` then we look into the query string parameters as well."""

        policy = TokenAuthenticationPolicy()
        pyramid_request.GET['access_token'] = 'valid123'
        pyramid_request.path = '/ws'

        result = policy.unauthenticated_userid(pyramid_request)

        assert result == 'acct:foo@example.com'

    def test_unauthenticated_userid_returns_none_for_invalid_query_param_token(self, pyramid_request):
        """When the path is `/ws` but the token is invalid, it should still return None."""

        policy = TokenAuthenticationPolicy()
        pyramid_request.GET['access_token'] = 'expired'
        pyramid_request.path = '/ws'

        result = policy.unauthenticated_userid(pyramid_request)

        assert result is None

    def test_unauthenticated_userid_skips_query_param_for_non_ws_requests(self, pyramid_request):
        """
        When we have a valid token in the `access_token` query param, but it's
        not a request to /ws, then we should ignore this access token.
        """

        policy = TokenAuthenticationPolicy()
        pyramid_request.GET['access_token'] = 'valid123'
        pyramid_request.path = '/api'

        result = policy.unauthenticated_userid(pyramid_request)

        assert result is None

    def test_authenticated_userid_uses_callback(self, pyramid_request):
        def callback(userid, request):
            return None
        policy = TokenAuthenticationPolicy(callback=callback)
        pyramid_request.auth_token = 'valid123'

        result = policy.authenticated_userid(pyramid_request)

        assert result is None

    def test_effective_principals_uses_callback(self, pyramid_request):
        def callback(userid, request):
            return [userid + '.foo', 'group:donkeys']
        policy = TokenAuthenticationPolicy(callback=callback)
        pyramid_request.auth_token = 'valid123'

        result = policy.effective_principals(pyramid_request)

        assert set(result) > set(['acct:foo@example.com',
                                  'acct:foo@example.com.foo',
                                  'group:donkeys'])

    @pytest.fixture
    def fake_token(self):
        return DummyToken()

    @pytest.fixture
    def token_service(self, pyramid_config, fake_token):
        def validate(token_str):
            if token_str == 'valid123':
                return fake_token
            return None
        svc = mock.Mock(validate=mock.Mock(side_effect=validate))
        pyramid_config.register_service(svc, name='auth_token')
        return svc


class DummyToken(object):
    def __init__(self, userid='acct:foo@example.com', valid=True):
        self.userid = userid
        self._valid = valid

    def is_valid(self):
        return self._valid
