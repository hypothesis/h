from unittest import mock

import pytest

from h import accounts


@pytest.mark.usefixtures("user_service")
class TestGetUser:
    def test_fetches_user_using_service(
        self, factories, pyramid_config, pyramid_request, user_service
    ):
        pyramid_config.testing_securitypolicy("userid")
        user_service.fetch.return_value = factories.User.build()

        accounts.get_user(pyramid_request)

        user_service.fetch.assert_called_once_with("userid")

    def test_does_not_invalidate_session_if_not_authenticated(self, pyramid_request):
        """
        If authenticated_userid is None it shouldn't invalidate the session.

        Even though the user with id None obviously won't exist in the db.

        This also tests that it doesn't raise a redirect in this case.

        """
        pyramid_request.session.invalidate = mock.Mock()

        accounts.get_user(pyramid_request)

        assert not pyramid_request.session.invalidate.called

    def test_returns_user(
        self, factories, pyramid_config, pyramid_request, user_service
    ):
        pyramid_config.testing_securitypolicy("userid")
        user = user_service.fetch.return_value = factories.User.build()

        result = accounts.get_user(pyramid_request)

        assert result == user
