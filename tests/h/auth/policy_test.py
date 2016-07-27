# -*- coding: utf-8 -*-

import mock
import pytest

from pyramid.interfaces import IAuthenticationPolicy

from h.auth.policy import AuthenticationPolicy
from h.auth.policy import TokenAuthenticationPolicy

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


@pytest.mark.usefixtures('api_token', 'jwt')
class TestTokenAuthenticationPolicy(object):
    def test_remember_does_nothing(self, pyramid_request):
        policy = TokenAuthenticationPolicy()

        assert policy.remember(pyramid_request, 'foo') == []

    def test_forget_does_nothing(self, pyramid_request):
        policy = TokenAuthenticationPolicy()

        assert policy.forget(pyramid_request) == []

    def test_unauthenticated_userid_is_none_if_header_missing(self, pyramid_request):
        policy = TokenAuthenticationPolicy()

        assert policy.unauthenticated_userid(pyramid_request) is None

    @pytest.mark.parametrize('value', [
        'junk header',
        'bearer:wibble',
        'Bearer',
        'Bearer ',
    ])
    def test_unauthenticated_userid_is_none_if_header_incorrectly_formatted(self, pyramid_request, value):
        policy = TokenAuthenticationPolicy()
        pyramid_request.headers = {'Authorization': value}

        assert policy.unauthenticated_userid(pyramid_request) is None

    def test_unauthenticated_userid_passes_token_to_extractor_functions(self, jwt, api_token, pyramid_request):
        policy = TokenAuthenticationPolicy()
        api_token.return_value = None
        jwt.return_value = None
        pyramid_request.headers = {'Authorization': 'Bearer f00ba12'}

        policy.unauthenticated_userid(pyramid_request)

        api_token.assert_called_once_with('f00ba12', pyramid_request)
        jwt.assert_called_once_with('f00ba12', pyramid_request)

    def test_unauthenticated_userid_returns_userid_from_api_token_if_present(self, jwt, api_token, pyramid_request):
        policy = TokenAuthenticationPolicy()
        api_token.return_value = 'acct:foo@example.com'
        jwt.return_value = 'acct:bar@example.com'
        pyramid_request.headers = {'Authorization': 'Bearer f00ba12'}

        result = policy.unauthenticated_userid(pyramid_request)

        assert result == 'acct:foo@example.com'

    def test_unauthenticated_userid_returns_userid_from_jwt_as_fallback(self, jwt, api_token, pyramid_request):
        policy = TokenAuthenticationPolicy()
        api_token.return_value = None
        jwt.return_value = 'acct:bar@example.com'
        pyramid_request.headers = {'Authorization': 'Bearer f00ba12'}

        result = policy.unauthenticated_userid(pyramid_request)

        assert result == 'acct:bar@example.com'

    def test_unauthenticated_userid_returns_none_if_neither_token_valid(self, jwt, api_token, pyramid_request):
        policy = TokenAuthenticationPolicy()
        api_token.return_value = None
        jwt.return_value = None
        pyramid_request.headers = {'Authorization': 'Bearer f00ba12'}

        result = policy.unauthenticated_userid(pyramid_request)

        assert result is None

    def test_authenticated_userid_uses_callback(self, jwt, api_token, pyramid_request):
        def callback(userid, request):
            return None
        policy = TokenAuthenticationPolicy(callback=callback)
        api_token.return_value = 'acct:foo@example.com'
        jwt.return_value = None
        pyramid_request.headers = {'Authorization': 'Bearer f00ba12'}

        result = policy.authenticated_userid(pyramid_request)

        assert result is None

    def test_effective_principals_uses_callback(self, jwt, api_token, pyramid_request):
        def callback(userid, request):
            return [userid + '.foo', 'group:donkeys']
        policy = TokenAuthenticationPolicy(callback=callback)
        api_token.return_value = 'acct:foo@example.com'
        jwt.return_value = None
        pyramid_request.headers = {'Authorization': 'Bearer f00ba12'}

        result = policy.effective_principals(pyramid_request)

        assert set(result) > set(['acct:foo@example.com',
                                  'acct:foo@example.com.foo',
                                  'group:donkeys'])

    @pytest.fixture
    def api_token(self, patch):
        return patch('h.auth.tokens.userid_from_api_token')

    @pytest.fixture
    def jwt(self, patch):
        return patch('h.auth.tokens.userid_from_jwt')
