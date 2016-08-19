# -*- coding: utf-8 -*-
import mock
import pytest
from pyramid import httpexceptions

from h import accounts


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
def user_service(pyramid_config):
    service = mock.Mock(spec_set=['fetch'])
    service.fetch.return_value = None
    pyramid_config.register_service(service, name='user')
    return service
