# -*- coding: utf-8 -*-
import mock
import pytest
from pyramid import httpexceptions

from h import accounts

# The fixtures required to mock all of get_user()'s dependencies.
get_user_fixtures = pytest.mark.usefixtures('util', 'get_by_username')


@get_user_fixtures
def test_get_user_calls_split_user(util):
    """It should call split_user() once with the given userid."""
    util.user.split_user.return_value = {
        'username': 'fred', 'domain': 'hypothes.is'}

    accounts.get_user('acct:fred@hypothes.is', mock.Mock())

    util.user.split_user.assert_called_once_with('acct:fred@hypothes.is')


@get_user_fixtures
def test_get_user_returns_None_if_split_user_raises_ValueError(util):
    util.user.split_user.side_effect = ValueError

    assert accounts.get_user('userid', mock.Mock()) is None


@get_user_fixtures
def test_get_user_returns_None_if_domain_does_not_match(util, pyramid_request):
    util.user.split_user.return_value = {
        'username': 'username', 'domain': 'other'}

    assert accounts.get_user('userid', pyramid_request) is None


@get_user_fixtures
def test_get_user_calls_get_by_username(util, get_by_username, pyramid_request):
    """It should call get_by_username() once with the username."""
    pyramid_request.auth_domain = 'hypothes.is'
    util.user.split_user.return_value = {
        'username': 'username', 'domain': 'hypothes.is'}

    accounts.get_user('acct:username@hypothes.is', pyramid_request)

    get_by_username.assert_called_once_with(pyramid_request.db, 'username')


@get_user_fixtures
def test_get_user_returns_user(util, get_by_username, pyramid_request):
    """It should return the result from get_by_username()."""
    pyramid_request.auth_domain = 'hypothes.is'
    util.user.split_user.return_value = {
        'username': 'username', 'domain': 'hypothes.is'}

    result = accounts.get_user('acct:username@hypothes.is', pyramid_request)

    assert result == get_by_username.return_value


@pytest.mark.usefixtures('user_service')
class TestAuthenticatedUser(object):
    def test_fetches_user_using_service(self,
                                        factories,
                                        pyramid_config,
                                        pyramid_request,
                                        user_service):
        pyramid_config.testing_securitypolicy('userid')
        user_service.fetch.return_value = factories.User()

        accounts.authenticated_user(pyramid_request)

        user_service.fetch.assert_called_once_with('userid')

    def test_invalidates_session_if_user_does_not_exist(self,
                                                        pyramid_config,
                                                        pyramid_request):
        """It should log the user out if they no longer exist in the db."""
        pyramid_request.session.invalidate = mock.Mock()
        pyramid_config.testing_securitypolicy('userid')

        try:
            accounts.authenticated_user(pyramid_request)
        except Exception:
            pass

        pyramid_request.session.invalidate.assert_called_once_with()

    def test_does_not_invalidate_session_if_not_authenticated(self,
                                                              pyramid_config,
                                                              pyramid_request):
        """
        If authenticated_userid is None it shouldn't invalidate the session.

        Even though the user with id None obviously won't exist in the db.

        This also tests that it doesn't raise a redirect in this case.

        """
        pyramid_request.session.invalidate = mock.Mock()

        accounts.authenticated_user(pyramid_request)

        assert not pyramid_request.session.invalidate.called

    def test_redirects_if_user_does_not_exist(self,
                                              pyramid_config,
                                              pyramid_request):
        pyramid_request.url = '/the/page/that/I/was/on'
        pyramid_config.testing_securitypolicy('userid')

        with pytest.raises(httpexceptions.HTTPFound) as exc:
            accounts.authenticated_user(pyramid_request)

        assert exc.value.location == '/the/page/that/I/was/on', (
            'It should redirect to the same page that was requested')

    def test_returns_user(self,
                          factories,
                          pyramid_config,
                          pyramid_request,
                          user_service):
        pyramid_config.testing_securitypolicy('userid')
        user = user_service.fetch.return_value = factories.User()

        result = accounts.authenticated_user(pyramid_request)

        assert result == user


@pytest.fixture
def util(patch):
    return patch('h.accounts.util')


@pytest.fixture
def get_by_username(patch):
    return patch('h.accounts.models.User.get_by_username', autospec=False)


@pytest.fixture
def user_service(pyramid_config):
    service = mock.Mock(spec_set=['fetch'])
    service.fetch.return_value = None
    pyramid_config.register_service(service, name='user')
    return service
