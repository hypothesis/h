# -*- coding: utf-8 -*-

import mock
from pyramid.authentication import SessionAuthenticationPolicy
from pyramid.testing import DummyRequest
import pytest

from h.auth.policy import AuthenticationPolicy

SESSION_AUTH_PATHS = (
    '/login',
    '/account/profile',
    '/api/badge',
    '/api/token',
)

TOKEN_AUTH_PATHS = (
    '/api',
    '/api/foo',
    '/api/annotations/abc123',
)


@pytest.mark.usefixtures('accounts', 'policy', 'tokens')
class TestAuthenticationPolicy(object):

    def test_authenticated_userid_delegates_for_session_auth_paths(self, session_request):
        result = self.policy.authenticated_userid(session_request)

        self.upstream_policy.authenticated_userid.assert_called_once_with(session_request)
        assert result == self.upstream_policy.authenticated_userid.return_value

    def test_authenticated_userid_uses_tokens_for_token_auth_paths(self, tokens, token_request):
        result = self.policy.authenticated_userid(token_request)

        tokens.authenticated_userid.assert_called_once_with(token_request)
        assert result == tokens.authenticated_userid.return_value

    def test_authenticated_userid_returns_None_if_user_does_not_exist(
            self, accounts, session_request, tokens, token_request):
        accounts.get_user.return_value = None
        tokens.authenticated_userid.return_value = 'acct:hugh@hypothes.is'
        self.upstream_policy.authenticated_userid.return_value = (
            'acct:hugh@hypothes.is')

        assert self.policy.authenticated_userid(session_request) is None
        assert self.policy.authenticated_userid(token_request) is None

    def test_authenticated_userid_calls_forget_if_user_does_not_exist(
            self, accounts, forget, session_request, tokens, token_request):
        accounts.get_user.return_value = None
        tokens.authenticated_userid.return_value = 'acct:hugh@hypothes.is'
        self.upstream_policy.authenticated_userid.return_value = (
            'acct:hugh@hypothes.is')

        self.policy.authenticated_userid(session_request)
        forget.assert_called_once_with(self.policy, session_request)

        self.policy.authenticated_userid(token_request)
        assert forget.call_count == 2
        assert forget.call_args == mock.call(self.policy, token_request)

    def test_unauthenticated_userid_delegates_for_session_auth_paths(self, session_request):
        result = self.policy.unauthenticated_userid(session_request)

        self.upstream_policy.unauthenticated_userid.assert_called_once_with(session_request)
        assert result == self.upstream_policy.unauthenticated_userid.return_value

    def test_unauthenticated_userid_uses_tokens_for_token_auth_paths(self, tokens, token_request):
        result = self.policy.unauthenticated_userid(token_request)

        tokens.authenticated_userid.assert_called_once_with(token_request)
        assert result == tokens.authenticated_userid.return_value

    def test_unauthenticated_userid_returns_None_if_user_does_not_exist(
            self, accounts, session_request, tokens, token_request):
        accounts.get_user.return_value = None
        tokens.authenticated_userid.return_value = 'acct:hugh@hypothes.is'
        self.upstream_policy.unauthenticated_userid.return_value = (
            'acct:hugh@hypothes.is')

        assert self.policy.unauthenticated_userid(session_request) is None
        assert self.policy.unauthenticated_userid(token_request) is None

    def test_unauthenticated_userid_calls_forget_if_user_does_not_exist(
            self, accounts, forget, session_request, tokens, token_request):
        accounts.get_user.return_value = None
        tokens.authenticated_userid.return_value = 'acct:hugh@hypothes.is'
        self.upstream_policy.unauthenticated_userid.return_value = (
            'acct:hugh@hypothes.is')

        self.policy.unauthenticated_userid(session_request)
        forget.assert_called_once_with(self.policy, session_request)

        self.policy.unauthenticated_userid(token_request)
        assert forget.call_count == 2
        assert forget.call_args == mock.call(self.policy, token_request)

    @mock.patch('h.auth.policy.util')
    def test_effective_principals_calls_effective_principals_with_authenticated_userid(self, util, authn_policy):
        authn_policy.authenticated_userid.return_value = 'acct:rami@example.com'
        request = DummyRequest()

        result = self.policy.effective_principals(request)

        util.effective_principals.assert_called_once_with('acct:rami@example.com', request)
        assert result == util.effective_principals.return_value

    def test_remember_delegates_for_session_auth_paths(self, session_request):
        result = self.policy.remember(session_request, 'foo', bar='baz')

        self.upstream_policy.remember.assert_called_once_with(session_request, 'foo', bar='baz')
        assert result == self.upstream_policy.remember.return_value

    def test_remember_does_nothing_for_token_auth_paths(self, token_request):
        result = self.policy.remember(token_request, 'foo', bar='baz')

        self.upstream_policy.remember.assert_not_called()
        assert result == []

    def test_forget_delegates_for_session_auth_paths(self, session_request):
        result = self.policy.forget(session_request)

        self.upstream_policy.forget.assert_called_once_with(session_request)
        assert result == self.upstream_policy.forget.return_value

    def test_forget_does_nothing_for_token_auth_paths(self, token_request):
        result = self.policy.forget(token_request)

        self.upstream_policy.forget.assert_not_called()
        assert result == []

    @pytest.fixture
    def accounts(self, patch):
        return patch('h.auth.policy.accounts')

    @pytest.fixture
    def forget(self, patch):
        return patch('h.auth.policy.AuthenticationPolicy.forget')

    @pytest.fixture
    def policy(self):
        self.upstream_policy = mock.Mock(spec_set=SessionAuthenticationPolicy())
        self.policy = AuthenticationPolicy()
        self.policy.session_policy = self.upstream_policy

    # session_request and token_request are parametrized fixtures, which will
    # take on each value in the passed `params` sequence in turn. This is a
    # quick and easy way to generate a named fixture which takes multiple
    # values and can be used by multiple tests.
    @pytest.fixture(params=SESSION_AUTH_PATHS)
    def session_request(self, request):
        return DummyRequest(path=request.param)

    @pytest.fixture
    def tokens(self, patch):
        return patch('h.auth.policy.tokens')

    @pytest.fixture(params=TOKEN_AUTH_PATHS)
    def token_request(self, request):
        return DummyRequest(path=request.param)
