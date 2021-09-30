from unittest.mock import sentinel

import pytest

from h.security import Identity
from h.security.policy.bearer_token import BearerTokenPolicy


@pytest.mark.usefixtures("user_service", "auth_token_service")
class TestBearerTokenPolicy:
    def test_identity(self, pyramid_request, auth_token_service, user_service):
        identity = BearerTokenPolicy().identity(pyramid_request)

        auth_token_service.get_bearer_token.assert_called_once_with(pyramid_request)
        auth_token_service.validate.assert_called_once_with(
            auth_token_service.get_bearer_token.return_value
        )
        user_service.fetch.assert_called_once_with(
            auth_token_service.validate.return_value.userid
        )
        assert identity == Identity.from_models(user=user_service.fetch.return_value)

    def test_identity_caches(self, pyramid_request, auth_token_service):
        policy = BearerTokenPolicy()

        policy.identity(pyramid_request)
        policy.identity(pyramid_request)

        auth_token_service.get_bearer_token.assert_called_once()

    def test_identity_for_webservice(self, pyramid_request, auth_token_service):
        pyramid_request.path = "/ws"
        pyramid_request.GET["access_token"] = sentinel.access_token

        BearerTokenPolicy().identity(pyramid_request)

        auth_token_service.get_bearer_token.assert_not_called()
        auth_token_service.validate.assert_called_once_with(sentinel.access_token)

    def test_identity_returns_None_with_no_token(
        self, pyramid_request, auth_token_service
    ):
        auth_token_service.get_bearer_token.return_value = None

        assert BearerTokenPolicy().identity(pyramid_request) is None

    def test_identity_returns_None_for_invalid_tokens(
        self, pyramid_request, auth_token_service
    ):
        auth_token_service.validate.return_value = None

        assert BearerTokenPolicy().identity(pyramid_request) is None

    def test_identity_returns_None_for_invalid_users(
        self, pyramid_request, user_service
    ):
        user_service.fetch.return_value = None

        assert BearerTokenPolicy().identity(pyramid_request) is None
