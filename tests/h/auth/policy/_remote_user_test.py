from unittest.mock import sentinel

import pytest

from h.auth.policy._remote_user import RemoteUserAuthenticationPolicy
from h.security import Identity


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
