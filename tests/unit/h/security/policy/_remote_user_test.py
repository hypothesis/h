from unittest.mock import sentinel

import pytest

from h.security import Identity
from h.security.policy._remote_user import RemoteUserPolicy


@pytest.mark.usefixtures("user_service")
class TestRemoteUserPolicy:
    def test_forget(self, pyramid_request):
        # pylint:disable=use-implicit-booleaness-not-comparison
        assert RemoteUserPolicy().forget(pyramid_request, foo="bar") == []

    def test_identity(self, pyramid_request, user_service):
        pyramid_request.environ["HTTP_X_FORWARDED_USER"] = sentinel.forwarded_user

        identity = RemoteUserPolicy().identity(pyramid_request)

        user_service.fetch.assert_called_once_with(sentinel.forwarded_user)
        assert identity == Identity.from_models(user=user_service.fetch.return_value)

    def test_identity_returns_None_for_no_forwarded_user(self, pyramid_request):
        pyramid_request.environ["HTTP_X_FORWARDED_USER"] = None

        assert RemoteUserPolicy().identity(pyramid_request) is None

    def test_identity_returns_None_for_no_user(self, pyramid_request, user_service):
        pyramid_request.environ["HTTP_X_FORWARDED_USER"] = sentinel.forwarded_user
        user_service.fetch.return_value = None

        assert RemoteUserPolicy().identity(pyramid_request) is None

    def test_identity_returns_None_for_user_marked_as_deleted(
        self, pyramid_request, user_service
    ):
        pyramid_request.environ["HTTP_X_FORWARDED_USER"] = sentinel.forwarded_user
        user_service.fetch.return_value.deleted = True

        assert RemoteUserPolicy().identity(pyramid_request) is None

    def test_remember(self, pyramid_request):
        # pylint:disable=use-implicit-booleaness-not-comparison
        assert (
            RemoteUserPolicy().remember(pyramid_request, sentinel.userid, foo="bar")
            == []
        )
