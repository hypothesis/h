import base64
from unittest.mock import sentinel

import pytest

from h.exceptions import InvalidUserId
from h.models.auth_client import GrantType
from h.security.policy._auth_client import AuthClientPolicy


@pytest.mark.usefixtures("user_service")
class TestAuthClientPolicy:
    @pytest.mark.parametrize("route_name,method", AuthClientPolicy.API_WHITELIST)
    def test_handles(self, pyramid_request, route_name, method):
        pyramid_request.matched_route.name = route_name
        pyramid_request.method = method

        assert AuthClientPolicy.handles(pyramid_request)

    def test_handles_rejects_unknown_routes(self, pyramid_request):
        pyramid_request.matched_route.name = "not.recognised"

        assert not AuthClientPolicy.handles(pyramid_request)

    def test_handles_rejects_no_route(self, pyramid_request):
        pyramid_request.matched_route = None

        assert not AuthClientPolicy.handles(pyramid_request)

    def test_identity(self, pyramid_request, auth_client, user_service, Identity):
        pyramid_request.headers["X-Forwarded-User"] = sentinel.forwarded_user

        identity = AuthClientPolicy().identity(pyramid_request)

        user_service.fetch.assert_called_once_with(sentinel.forwarded_user)
        Identity.from_models.assert_called_once_with(
            auth_client=auth_client, user=user_service.fetch.return_value
        )
        assert identity == Identity.from_models.return_value

    def test_identify_without_forwarded_user(
        self, pyramid_request, auth_client, Identity
    ):
        pyramid_request.headers["X-Forwarded-User"] = None

        identity = AuthClientPolicy().identity(pyramid_request)

        Identity.from_models.assert_called_once_with(auth_client=auth_client, user=None)
        assert identity == Identity.from_models.return_value

    def test_identity_returns_None_without_credentials(self, pyramid_request):
        pyramid_request.headers["Authorization"] = None

        assert AuthClientPolicy().identity(pyramid_request) is None

    def test_identity_returns_None_if_auth_client_id_is_invalid(
        self, pyramid_request, auth_client, db_session
    ):
        db_session.delete(auth_client)
        db_session.flush()

        assert AuthClientPolicy().identity(pyramid_request) is None

    def test_identity_returns_None_if_auth_client_missing(
        self, pyramid_request, auth_client, db_session
    ):
        db_session.delete(auth_client)
        db_session.flush()

        assert AuthClientPolicy().identity(pyramid_request) is None

    def test_identify_returns_None_if_auth_client_not_secret(
        self, auth_client, pyramid_request
    ):
        self.set_http_credentials(pyramid_request, "NOT A UUID", auth_client.secret)

        assert AuthClientPolicy().identity(pyramid_request) is None

    def test_identify_returns_None_if_auth_client_not_client_type(
        self, auth_client, pyramid_request
    ):
        auth_client.grant_type = None

        assert AuthClientPolicy().identity(pyramid_request) is None

    def test_identify_returns_None_if_auth_client_secret_is_None(
        self, auth_client, pyramid_request
    ):
        auth_client.secret = None

        assert AuthClientPolicy().identity(pyramid_request) is None

    def test_identify_returns_None_if_auth_client_secrets_do_not_match(
        self, auth_client, pyramid_request
    ):
        self.set_http_credentials(pyramid_request, auth_client.id, "WRONG SECRET")

        assert AuthClientPolicy().identity(pyramid_request) is None

    def test_identify_returns_None_if_forwarded_user_is_not_found(
        self, user_service, pyramid_request
    ):
        user_service.fetch.return_value = None

        assert AuthClientPolicy().identity(pyramid_request) is None

    def test_identify_returns_None_if_forwarded_user_is_marked_as_deleted(
        self, user_service, pyramid_request
    ):
        user_service.fetch.return_value.deleted = True

        assert AuthClientPolicy().identity(pyramid_request) is None

    def test_identify_returns_None_if_forwarded_userid_is_invalid(
        self, user_service, pyramid_request
    ):
        user_service.fetch.side_effect = InvalidUserId(sentinel.invalid_id)

        assert AuthClientPolicy().identity(pyramid_request) is None

    def test_identify_returns_None_on_forwarded_userid_authority_mismatch(
        self, user, auth_client, pyramid_request
    ):
        user.authority = "not" + auth_client.authority

        assert AuthClientPolicy().identity(pyramid_request) is None

    @pytest.fixture
    def auth_client(self, factories):
        return factories.ConfidentialAuthClient(grant_type=GrantType.client_credentials)

    @pytest.fixture(autouse=True)
    def with_credentials(self, pyramid_request, auth_client):
        self.set_http_credentials(pyramid_request, auth_client.id, auth_client.secret)
        pyramid_request.headers["X-Forwarded-User"] = sentinel.forwarded_user

    @classmethod
    def set_http_credentials(cls, pyramid_request, client_id, client_secret):
        encoded = base64.standard_b64encode(
            f"{client_id}:{client_secret}".encode("utf-8")
        )
        creds = encoded.decode("ascii")
        pyramid_request.headers["Authorization"] = f"Basic {creds}"

    @pytest.fixture(autouse=True)
    def user(self, factories, auth_client, user_service):
        user = factories.User(authority=auth_client.authority)
        user_service.fetch.return_value = user
        return user


@pytest.fixture(autouse=True)
def Identity(mocker):
    return mocker.patch(
        "h.security.policy._auth_client.Identity", autospec=True, spec_set=True
    )
