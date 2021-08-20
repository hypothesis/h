from unittest.mock import sentinel

import pytest

from h.auth.policy.bearer_token import TokenPolicy
from h.security import Identity


@pytest.mark.usefixtures("user_service", "auth_token_service")
class TestTokenPolicy:
    def test_identity(self, pyramid_request, auth_token_service, user_service):
        pyramid_request.auth_token = sentinel.auth_token

        identity = TokenPolicy().identity(pyramid_request)

        auth_token_service.validate.assert_called_once_with(sentinel.auth_token)
        user_service.fetch.assert_called_once_with(
            auth_token_service.validate.return_value.userid
        )
        assert identity == Identity(user=user_service.fetch.return_value)

    def test_identity_for_webservice(self, pyramid_request, auth_token_service):
        pyramid_request.auth_token = sentinel.decoy
        pyramid_request.path = "/ws"
        pyramid_request.GET["access_token"] = sentinel.access_token

        TokenPolicy().identity(pyramid_request)

        auth_token_service.validate.assert_called_once_with(sentinel.access_token)

    def test_identity_returns_None_with_no_token(self, pyramid_request):
        pyramid_request.auth_token = None

        assert TokenPolicy().identity(pyramid_request) is None

    def test_identity_returns_None_for_invalid_tokens(
        self, pyramid_request, auth_token_service
    ):
        pyramid_request.auth_token = sentinel.auth_token
        auth_token_service.validate.return_value = None

        assert TokenPolicy().identity(pyramid_request) is None

    def test_identity_returns_None_for_invalid_users(
        self, pyramid_request, user_service
    ):
        pyramid_request.auth_token = sentinel.auth_token
        user_service.fetch.return_value = None

        assert TokenPolicy().identity(pyramid_request) is None
