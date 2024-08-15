from unittest.mock import sentinel

import pytest

from h.security.policy._bearer_token import BearerTokenPolicy


@pytest.mark.usefixtures("user_service", "auth_token_service")
class TestBearerTokenPolicy:
    @pytest.mark.parametrize(
        "is_api_request_return_value,expected_result",
        [
            (True, True),
            (False, False),
        ],
    )
    def test_handles(
        self,
        is_api_request,
        is_api_request_return_value,
        expected_result,
        pyramid_request,
    ):
        is_api_request.return_value = is_api_request_return_value

        assert BearerTokenPolicy.handles(pyramid_request) == expected_result

    def test_identity(
        self, pyramid_request, auth_token_service, user_service, Identity
    ):
        identity = BearerTokenPolicy().identity(pyramid_request)

        auth_token_service.get_bearer_token.assert_called_once_with(pyramid_request)
        auth_token_service.validate.assert_called_once_with(
            auth_token_service.get_bearer_token.return_value
        )
        user_service.fetch.assert_called_once_with(
            auth_token_service.validate.return_value.userid
        )
        Identity.from_models.assert_called_once_with(
            user=user_service.fetch.return_value
        )
        assert identity == Identity.from_models.return_value

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

    def test_identity_returns_None_for_user_marked_as_deleted(
        self, pyramid_request, user_service
    ):
        user_service.fetch.return_value.deleted = True

        assert BearerTokenPolicy().identity(pyramid_request) is None


@pytest.fixture(autouse=True)
def is_api_request(mocker):
    return mocker.patch("h.security.policy._bearer_token.is_api_request", autospec=True)


@pytest.fixture(autouse=True)
def Identity(mocker):
    return mocker.patch(
        "h.security.policy._bearer_token.Identity", autospec=True, spec_set=True
    )
