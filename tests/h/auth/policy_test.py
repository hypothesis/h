# -*- coding: utf-8 -*-

import mock
from pyramid.authentication import SessionAuthenticationPolicy
import pytest

from h.auth.policy import AuthenticationPolicy
from h.auth.policy import TokenAuthenticationPolicy

SESSION_AUTH_PATHS = (
    '/login',
    '/account/settings',
    '/api/badge',
    '/api/token',
)

TOKEN_AUTH_PATHS = (
    '/api',
    '/api/foo',
    '/api/annotations/abc123',
)


class TestAuthenticationPolicy(object):

    @pytest.fixture(autouse=True)
    def policy(self):
        self.session_policy = mock.Mock(spec_set=SessionAuthenticationPolicy())
        self.token_policy = mock.Mock(spec_set=TokenAuthenticationPolicy())
        self.policy = AuthenticationPolicy()
        self.policy.session_policy = self.session_policy
        self.policy.token_policy = self.token_policy

    # session_request and token_request are parametrized fixtures, which will
    # take on each value in the passed `params` sequence in turn. This is a
    # quick and easy way to generate a named fixture which takes multiple
    # values and can be used by multiple tests.
    @pytest.fixture(params=SESSION_AUTH_PATHS)
    def session_request(self, request, pyramid_request):
        pyramid_request.path = request.param
        return pyramid_request

    @pytest.fixture(params=TOKEN_AUTH_PATHS)
    def token_request(self, request, pyramid_request):
        pyramid_request.path = request.param
        return pyramid_request

    def test_authenticated_userid_uses_session_policy_for_session_auth_paths(self, session_request):
        result = self.policy.authenticated_userid(session_request)

        self.session_policy.authenticated_userid.assert_called_once_with(session_request)
        assert result == self.session_policy.authenticated_userid.return_value

    def test_authenticated_userid_uses_token_policy_for_token_auth_paths(self, token_request):
        result = self.policy.authenticated_userid(token_request)

        self.token_policy.authenticated_userid.assert_called_once_with(token_request)
        assert result == self.token_policy.authenticated_userid.return_value

    def test_unauthenticated_userid_uses_session_policy_for_session_auth_paths(self, session_request):
        result = self.policy.unauthenticated_userid(session_request)

        self.session_policy.unauthenticated_userid.assert_called_once_with(session_request)
        assert result == self.session_policy.unauthenticated_userid.return_value

    def test_unauthenticated_userid_uses_token_policy_for_token_auth_paths(self, token_request):
        result = self.policy.unauthenticated_userid(token_request)

        self.token_policy.unauthenticated_userid.assert_called_once_with(token_request)
        assert result == self.token_policy.unauthenticated_userid.return_value

    def test_effective_principals_uses_session_policy_for_session_auth_paths(self, session_request):
        result = self.policy.effective_principals(session_request)

        self.session_policy.effective_principals.assert_called_once_with(session_request)
        assert result == self.session_policy.effective_principals.return_value

    def test_effective_principals_uses_token_policy_for_token_auth_paths(self, token_request):
        result = self.policy.effective_principals(token_request)

        self.token_policy.effective_principals.assert_called_once_with(token_request)
        assert result == self.token_policy.effective_principals.return_value

    def test_remember_uses_session_policy_for_session_auth_paths(self, session_request):
        result = self.policy.remember(session_request, 'foo', bar='baz')

        self.session_policy.remember.assert_called_once_with(session_request, 'foo', bar='baz')
        assert result == self.session_policy.remember.return_value

    def test_remember_uses_token_policy_for_token_auth_paths(self, token_request):
        result = self.policy.remember(token_request, 'foo', bar='baz')

        self.token_policy.remember.assert_called_once_with(token_request, 'foo', bar='baz')
        assert result == self.token_policy.remember.return_value

    def test_forget_uses_session_policy_for_session_auth_paths(self, session_request):
        result = self.policy.forget(session_request)

        self.session_policy.forget.assert_called_once_with(session_request)
        assert result == self.session_policy.forget.return_value

    def test_forget_uses_token_policy_for_token_auth_paths(self, token_request):
        result = self.policy.forget(token_request)

        self.token_policy.forget.assert_called_once_with(token_request)
        assert result == self.token_policy.forget.return_value


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
