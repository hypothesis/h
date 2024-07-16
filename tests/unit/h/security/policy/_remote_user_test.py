from unittest.mock import sentinel

import pytest

from h.security import Identity
from h.security.policy._remote_user import RemoteUserPolicy


@pytest.mark.usefixtures("user_service")
class TestRemoteUserPolicy:
    @pytest.mark.parametrize(
        "is_api_request_return_value,proxy_auth,expected_result",
        [
            (False, False, False),
            (False, True, True),
            (True, False, False),
            (True, True, False),
        ],
    )
    def test_handles(
        self,
        is_api_request,
        is_api_request_return_value,
        proxy_auth,
        expected_result,
        pyramid_request,
    ):
        is_api_request.return_value = is_api_request_return_value
        pyramid_request.registry.settings["h.proxy_auth"] = proxy_auth

        assert RemoteUserPolicy.handles(pyramid_request) == expected_result

    def test_handles_when_no_proxy_auth_setting(self, pyramid_request, is_api_request):
        is_api_request.return_value = False

        assert RemoteUserPolicy.handles(pyramid_request) is False

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

    @pytest.fixture(autouse=True)
    def is_api_request(self, mocker):
        return mocker.patch("h.security.policy._remote_user.is_api_request")
