# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import mock
import pytest
import base64

from pyramid.interfaces import IAuthenticationPolicy
from pyramid.security import (
    Everyone,
    Authenticated
)

from h.auth.policy import AuthenticationPolicy
from h.auth.policy import TokenAuthenticationPolicy
from h.auth.policy import APIAuthenticationPolicy
from h.auth.policy import AuthClientPolicy
from h.auth.policy import AUTH_CLIENT_API_WHITELIST

from h.services.user import UserService

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

AUTH_CLIENT_API_BLACKLIST = [
    ('api.groups', 'GET'),
    ('api.user', 'POST'),
    ('group_create', 'POST'),
    ('api.group_member', 'DELETE')
]


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


class TestAPIAuthenticationPolicy(object):

    def test_authenticated_userid_proxies_to_user_policy_first(self,
                                                               pyramid_request,
                                                               api_policy,
                                                               user_policy,
                                                               client_policy):
        userid = api_policy.authenticated_userid(pyramid_request)

        user_policy.authenticated_userid.assert_called_once_with(pyramid_request)
        assert client_policy.authenticated_userid.call_count == 0
        assert userid == user_policy.authenticated_userid.return_value

    @pytest.mark.parametrize('route_name,route_method', AUTH_CLIENT_API_WHITELIST)
    def test_authenticated_userid_proxies_to_client_policy_if_user_fails(self,
                                                                         pyramid_request,
                                                                         api_policy,
                                                                         user_policy,
                                                                         client_policy,
                                                                         route_name,
                                                                         route_method):
        pyramid_request.method = route_method
        pyramid_request.matched_route.name = route_name
        user_policy.authenticated_userid.return_value = None

        userid = api_policy.authenticated_userid(pyramid_request)

        user_policy.authenticated_userid.assert_called_once_with(pyramid_request)
        client_policy.authenticated_userid.assert_called_once_with(pyramid_request)
        assert userid == client_policy.authenticated_userid.return_value

    @pytest.mark.parametrize('route_name,route_method', AUTH_CLIENT_API_BLACKLIST)
    def test_authenticated_userid_does_not_proxy_to_client_policy_if_path_mismatch(self,
                                                                                   pyramid_request,
                                                                                   api_policy,
                                                                                   user_policy,
                                                                                   client_policy,
                                                                                   route_name,
                                                                                   route_method):
        pyramid_request.method = route_method
        pyramid_request.matched_route.name = route_name
        user_policy.authenticated_userid.return_value = None

        userid = api_policy.authenticated_userid(pyramid_request)

        user_policy.authenticated_userid.assert_called_once_with(pyramid_request)
        assert client_policy.authenticated_userid.call_count == 0
        assert userid == user_policy.authenticated_userid.return_value

    @pytest.mark.parametrize('route_name,route_method', AUTH_CLIENT_API_WHITELIST)
    def test_unauthenticated_userid_proxies_to_user_policy_first(self,
                                                                 pyramid_request,
                                                                 api_policy,
                                                                 user_policy,
                                                                 client_policy,
                                                                 route_name,
                                                                 route_method):
        pyramid_request.method = route_method
        pyramid_request.matched_route.name = route_name
        userid = api_policy.unauthenticated_userid(pyramid_request)

        user_policy.unauthenticated_userid.assert_called_once_with(pyramid_request)
        assert client_policy.unauthenticated_userid.call_count == 0
        assert userid == user_policy.unauthenticated_userid.return_value

    def test_unauthenticated_userid_proxies_to_client_policy_if_user_fails(self,
                                                                           pyramid_request,
                                                                           api_policy,
                                                                           user_policy,
                                                                           client_policy):
        user_policy.unauthenticated_userid.return_value = None

        userid = api_policy.unauthenticated_userid(pyramid_request)

        user_policy.unauthenticated_userid.assert_called_once_with(pyramid_request)
        client_policy.unauthenticated_userid.assert_called_once_with(pyramid_request)
        assert userid == client_policy.unauthenticated_userid.return_value

    @pytest.mark.parametrize('route_name,route_method', AUTH_CLIENT_API_BLACKLIST)
    def test_unauthenticated_userid_does_not_proxy_to_client_policy_if_path_mismatch(self,
                                                                                     pyramid_request,
                                                                                     api_policy,
                                                                                     user_policy,
                                                                                     client_policy,
                                                                                     route_name,
                                                                                     route_method):
        pyramid_request.method = route_method
        pyramid_request.matched_route.name = route_name
        user_policy.unauthenticated_userid.return_value = None

        userid = api_policy.unauthenticated_userid(pyramid_request)

        user_policy.unauthenticated_userid.assert_called_once_with(pyramid_request)
        assert client_policy.unauthenticated_userid.call_count == 0
        assert userid == user_policy.unauthenticated_userid.return_value

    def test_effective_principals_proxies_to_user_policy_first(self,
                                                               pyramid_request,
                                                               api_policy,
                                                               user_policy,
                                                               client_policy):
        user_policy.effective_principals.return_value = [Everyone, Authenticated]

        principals = api_policy.effective_principals(pyramid_request)

        user_policy.effective_principals.assert_called_once_with(pyramid_request)
        assert client_policy.effective_principals.call_count == 0
        assert principals == user_policy.effective_principals.return_value

    @pytest.mark.parametrize('route_name,route_method', AUTH_CLIENT_API_WHITELIST)
    def test_effective_principals_proxies_to_client_if_auth_principal_missing(self,
                                                                              pyramid_request,
                                                                              api_policy,
                                                                              user_policy,
                                                                              client_policy,
                                                                              route_name,
                                                                              route_method):
        pyramid_request.method = route_method
        pyramid_request.matched_route.name = route_name
        user_policy.effective_principals.return_value = [Everyone]

        principals = api_policy.effective_principals(pyramid_request)

        user_policy.effective_principals.assert_called_once_with(pyramid_request)
        client_policy.effective_principals.assert_called_once_with(pyramid_request)
        assert principals == client_policy.effective_principals.return_value

    @pytest.mark.parametrize('route_name,route_method', AUTH_CLIENT_API_BLACKLIST)
    def test_effective_principals_does_not_proxy_to_client_if_path_mismatch(self,
                                                                            pyramid_request,
                                                                            api_policy,
                                                                            user_policy,
                                                                            client_policy,
                                                                            route_name,
                                                                            route_method):
        pyramid_request.method = route_method
        pyramid_request.matched_route.name = route_name
        user_policy.effective_principals.return_value = [Everyone]

        principals = api_policy.effective_principals(pyramid_request)

        user_policy.effective_principals.assert_called_once_with(pyramid_request)
        assert client_policy.effective_principals.call_count == 0
        assert principals == user_policy.effective_principals.return_value

    @pytest.mark.parametrize('route_name,route_method', AUTH_CLIENT_API_WHITELIST)
    def test_remember_proxies_to_user_policy_first(self,
                                                   pyramid_request,
                                                   api_policy,
                                                   user_policy,
                                                   route_name,
                                                   route_method):
        pyramid_request.method = route_method
        pyramid_request.matched_route.name = route_name
        remembered = api_policy.remember(pyramid_request, 'acct:foo@bar.com')

        user_policy.remember.assert_called_once_with(pyramid_request, 'acct:foo@bar.com')
        assert remembered == user_policy.remember.return_value

    def test_remember_proxies_to_client_policy_second(self, pyramid_request, api_policy, user_policy, client_policy):
        user_policy.remember.return_value = []

        remembered = api_policy.remember(pyramid_request, 'acct:foo@bar.com')

        user_policy.remember.assert_called_once_with(pyramid_request, 'acct:foo@bar.com')
        client_policy.remember.assert_called_once_with(pyramid_request, 'acct:foo@bar.com')
        assert remembered == client_policy.remember.return_value

    @pytest.mark.parametrize('route_name,route_method', AUTH_CLIENT_API_BLACKLIST)
    def test_remember_does_not_proxy_to_client_if_path_mismatch(self,
                                                                pyramid_request,
                                                                api_policy,
                                                                user_policy,
                                                                client_policy,
                                                                route_name,
                                                                route_method):
        pyramid_request.method = route_method
        pyramid_request.matched_route.name = route_name
        user_policy.remember.return_value = []

        remembered = api_policy.remember(pyramid_request, 'acct:foo@bar.com')

        user_policy.remember.assert_called_once_with(pyramid_request, 'acct:foo@bar.com')
        assert client_policy.remember.call_count == 0
        assert remembered == user_policy.remember.return_value

    @pytest.mark.parametrize('route_name,route_method', AUTH_CLIENT_API_WHITELIST)
    def test_forget_proxies_to_user_policy_first(self,
                                                 pyramid_request,
                                                 api_policy,
                                                 user_policy,
                                                 route_name,
                                                 route_method):
        pyramid_request.method = route_method
        pyramid_request.matched_route.name = route_name
        forgot = api_policy.forget(pyramid_request)

        user_policy.forget.assert_called_once_with(pyramid_request)
        assert forgot == user_policy.forget.return_value

    def test_forget_proxies_to_client_policy_second(self, pyramid_request, api_policy, user_policy, client_policy):
        user_policy.forget.return_value = []

        forgot = api_policy.forget(pyramid_request)

        user_policy.forget.assert_called_once_with(pyramid_request)
        client_policy.forget.assert_called_once_with(pyramid_request)
        assert forgot == client_policy.forget.return_value

    @pytest.mark.parametrize('route_name,route_method', AUTH_CLIENT_API_BLACKLIST)
    def test_forget_does_not_proxy_to_client_if_path_mismatch(self,
                                                              pyramid_request,
                                                              api_policy,
                                                              user_policy,
                                                              client_policy,
                                                              route_name,
                                                              route_method):
        pyramid_request.method = route_method
        pyramid_request.matched_route.name = route_name
        user_policy.forget.return_value = []

        forgot = api_policy.forget(pyramid_request)

        user_policy.forget.assert_called_once_with(pyramid_request)
        assert client_policy.forget.call_count == 0
        assert forgot == user_policy.forget.return_value

    @pytest.fixture
    def client_policy(self):
        return mock.create_autospec(AuthClientPolicy, instance=True, spec_set=True)

    @pytest.fixture
    def user_policy(self):
        return mock.create_autospec(TokenAuthenticationPolicy, instance=True, spec_set=True)

    @pytest.fixture
    def api_policy(self, client_policy, user_policy):
        return APIAuthenticationPolicy(user_policy=user_policy,
                                        client_policy=client_policy)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.matched_route.name = 'api.groups'
        pyramid_request.method = 'POST'
        return pyramid_request


class TestAuthClientAuthenticationPolicy(object):

    def test_it_instantiates_a_BasicAuthAuthenticationPolicy(self, BasicAuthAuthenticationPolicy):
        AuthClientPolicy()

        BasicAuthAuthenticationPolicy.assert_called_once_with(check=AuthClientPolicy.check)

    def test_unauthenticated_userid_returns_forwarded_user_if_present(self, auth_policy, pyramid_request):
        pyramid_request.headers['X-Forwarded-User'] = 'filbert'

        userid = auth_policy.unauthenticated_userid(pyramid_request)

        assert userid == 'filbert'

    def test_unauthenticated_userid_returns_clientid_if_no_forwarded_user(self,
                                                                          auth_policy,
                                                                          pyramid_request,
                                                                          auth_client):
        userid = auth_policy.unauthenticated_userid(pyramid_request)

        assert userid == auth_client.id

    def test_unauthenticated_userid_proxies_to_basic_auth_if_no_forwarded_user(self,
                                                                               pyramid_request,
                                                                               BasicAuthAuthenticationPolicy):
        auth_policy = AuthClientPolicy()
        unauth_id = auth_policy.unauthenticated_userid(pyramid_request)

        BasicAuthAuthenticationPolicy.return_value.unauthenticated_userid.assert_called_once_with(pyramid_request)
        assert unauth_id == BasicAuthAuthenticationPolicy.return_value.unauthenticated_userid.return_value

    def test_unauthenticated_userid_doesnt_proxy_to_basic_auth_if_forwarded_user(self,
                                                                                pyramid_request,
                                                                                BasicAuthAuthenticationPolicy):
        pyramid_request.headers['X-Forwarded-User'] = 'dingbat'
        auth_policy = AuthClientPolicy()

        auth_policy.unauthenticated_userid(pyramid_request)

        assert BasicAuthAuthenticationPolicy.return_value.unauthenticated_userid.call_count == 0

    def test_authenticated_userid_returns_None_if_no_forwarded_userid(self, auth_policy, pyramid_request):
        userid = auth_policy.authenticated_userid(pyramid_request)

        assert userid is None

    def test_authenticated_userid_proxies_to_basic_auth_policy_if_forwarded_user(self,
                                                                                 pyramid_request,
                                                                                 BasicAuthAuthenticationPolicy):
        pyramid_request.headers['X-Forwarded-User'] = 'dingbat'
        auth_policy = AuthClientPolicy()
        auth_policy.authenticated_userid(pyramid_request)

        BasicAuthAuthenticationPolicy.return_value.unauthenticated_userid.assert_called_once_with(pyramid_request)
        BasicAuthAuthenticationPolicy.return_value.callback.assert_called_once_with(
            BasicAuthAuthenticationPolicy.return_value.unauthenticated_userid.return_value,
            pyramid_request)

    def test_authenticated_userid_does_not_proxy_if_no_forwarded_user(self,
                                                                      pyramid_request,
                                                                      BasicAuthAuthenticationPolicy):
        auth_policy = AuthClientPolicy()
        auth_policy.authenticated_userid(pyramid_request)

        assert BasicAuthAuthenticationPolicy.return_value.unauthenticated_userid.call_count == 0
        assert BasicAuthAuthenticationPolicy.return_value.callback.call_count == 0

    def test_authenticated_userid_returns_userid_if_callback_ok(self,
                                                                auth_policy,
                                                                pyramid_request):
        # check callback is mocked to return [], which is "OK"
        pyramid_request.headers['X-Forwarded-User'] = 'dingbat'

        userid = auth_policy.authenticated_userid(pyramid_request)

        assert userid == 'dingbat'

    def test_authenticated_userid_returns_None_if_callback_not_OK(self,
                                                                  check,
                                                                  pyramid_request):
        check.return_value = None
        policy = AuthClientPolicy(check=check)

        pyramid_request.headers['X-Forwarded-User'] = 'dingbat'

        userid = policy.authenticated_userid(pyramid_request)

        assert userid is None

    def test_effective_principals_proxies_to_basic_auth(self, pyramid_request, check, BasicAuthAuthenticationPolicy):
        auth_policy = AuthClientPolicy()
        auth_policy.effective_principals(pyramid_request)

        BasicAuthAuthenticationPolicy.return_value.effective_principals.assert_called_once_with(pyramid_request)

    def test_effective_principals_returns_list_containing_callback_return_value(self, pyramid_request, check):
        check.return_value = ['foople', 'blueberry']
        policy = AuthClientPolicy(check=check)

        principals = policy.effective_principals(pyramid_request)

        assert 'foople' in principals
        assert 'blueberry' in principals

    def test_effective_principals_returns_only_Everyone_if_callback_returns_None(self, pyramid_request, check):
        check.return_value = None
        policy = AuthClientPolicy(check=check)

        principals = policy.effective_principals(pyramid_request)

        assert principals == ['system.Everyone']

    def test_forget_does_nothing(self, auth_policy, pyramid_request):
        assert auth_policy.forget(pyramid_request) == []

    def test_remember_does_nothing(self, auth_policy, pyramid_request):
        assert auth_policy.remember(pyramid_request, 'whoever') == []

    def test_check_proxies_to_verify_auth_client(self, pyramid_request, verify_auth_client):
        AuthClientPolicy.check('someusername', 'somepassword', pyramid_request)

        verify_auth_client.assert_called_once_with('someusername', 'somepassword', pyramid_request.db)

    def test_check_returns_None_if_verify_auth_client_fails(self, pyramid_request, verify_auth_client):
        verify_auth_client.return_value = None

        principals = AuthClientPolicy.check('someusername', 'somepassword', pyramid_request)

        assert principals is None

    def test_check_proxies_to_principals_for_auth_client_if_no_forwarded_user(self,
                                                                              pyramid_request,
                                                                              verify_auth_client,
                                                                              principals_for_auth_client):

        principals = AuthClientPolicy.check('someusername', 'somepassword', pyramid_request)

        assert principals == principals_for_auth_client.return_value
        principals_for_auth_client.assert_called_once_with(verify_auth_client.return_value)

    def test_check_doesnt_proxy_to_principals_for_auth_client_if_forwarded_user(self,
                                                                                user_service,
                                                                                pyramid_request,
                                                                                verify_auth_client,
                                                                                principals_for_auth_client):
        pyramid_request.headers['X-Forwarded-User'] = 'acct:flop@woebang.baz'

        AuthClientPolicy.check('someusername', 'somepassword', pyramid_request)

        assert principals_for_auth_client.call_count == 0

    def test_check_fetches_user_if_forwarded_user(self,
                                                  pyramid_request,
                                                  verify_auth_client,
                                                  user_service):

        pyramid_request.headers['X-Forwarded-User'] = 'acct:flop@woebang.baz'

        AuthClientPolicy.check('someusername', 'somepassword', pyramid_request)

        user_service.fetch.assert_called_once_with('acct:flop@woebang.baz')

    def test_check_returns_None_if_user_fetch_raises_valueError(self,
                                                                pyramid_request,
                                                                verify_auth_client,
                                                                user_service):

        pyramid_request.headers['X-Forwarded-User'] = 'flop@woebang.baz'
        user_service.fetch.side_effect = ValueError('whoops')

        principals = AuthClientPolicy.check('someusername', 'somepassword', pyramid_request)

        assert principals is None

    def test_check_returns_None_if_fetch_forwarded_user_fails(self,
                                                              pyramid_request,
                                                              verify_auth_client,
                                                              user_service):
        user_service.fetch.return_value = None
        pyramid_request.headers['X-Forwarded-User'] = 'acct:flop@woebang.baz'

        principals = AuthClientPolicy.check('someusername', 'somepassword', pyramid_request)

        assert principals is None

    def test_check_returns_None_if_forwarded_user_authority_mismatch(self,
                                                                     pyramid_request,
                                                                     verify_auth_client,
                                                                     user_service,
                                                                     factories):
        mismatched_user = factories.User(authority="two.com")
        verify_auth_client.return_value = factories.ConfidentialAuthClient(authority="one.com")
        user_service.fetch.return_value = mismatched_user
        pyramid_request.headers['X-Forwarded-User'] = mismatched_user.userid

        principals = AuthClientPolicy.check('someusername', 'somepassword', pyramid_request)

        assert principals is None

    def test_it_proxies_to_principals_for_user_if_fetch_forwarded_user_ok(self,
                                                                          pyramid_request,
                                                                          verify_auth_client,
                                                                          user_service,
                                                                          factories,
                                                                          principals_for_auth_client_user):
        matched_user = factories.User(authority="one.com")
        verify_auth_client.return_value = factories.ConfidentialAuthClient(authority="one.com")
        user_service.fetch.return_value = matched_user
        pyramid_request.headers['X-Forwarded-User'] = matched_user.userid

        principals = AuthClientPolicy.check('someusername', 'somepassword', pyramid_request)

        principals_for_auth_client_user.assert_called_once_with(matched_user,
                                                                verify_auth_client.return_value)
        assert principals == principals_for_auth_client_user.return_value

    @pytest.fixture
    def user_service(self, pyramid_config):
        service = mock.create_autospec(UserService, spec_set=True, instance=True)
        service.fetch.return_value = None
        pyramid_config.register_service(service, name='user')
        return service

    @pytest.fixture
    def principals_for_auth_client(self, patch):
        return patch('h.auth.util.principals_for_auth_client')

    @pytest.fixture
    def principals_for_auth_client_user(self, patch):
        return patch('h.auth.util.principals_for_auth_client_user')

    @pytest.fixture
    def verify_auth_client(self, patch):
        return patch('h.auth.util.verify_auth_client')

    @pytest.fixture
    def check(self):
        check = mock.create_autospec(AuthClientPolicy.check, spec_set=True, instance=True)
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
            client_id=auth_client.id,
            client_secret=auth_client.secret)
        encoded = base64.standard_b64encode(user_pass.encode('utf-8'))
        pyramid_request.headers['Authorization'] = "Basic {creds}".format(creds=encoded.decode('ascii'))
        return pyramid_request

    @pytest.fixture
    def BasicAuthAuthenticationPolicy(self, patch):
        return patch('h.auth.policy.BasicAuthAuthenticationPolicy')


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
