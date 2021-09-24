import json
from calendar import timegm
from datetime import datetime, timedelta
from unittest import mock

import jwt
import pytest
from oauthlib.common import Request as OAuthRequest
from oauthlib.oauth2.rfc6749 import errors

from h.services.oauth._jwt_grant import JWTAuthorizationGrant
from h.services.oauth._validator import Client
from h.services.user import user_service_factory


class TestJWTAuthorizationGrantCreateTokenResponse:
    def test_returns_error_when_validation_fails(
        self, grant, oauth_request, token_handler, authclient
    ):
        authclient.secret = None
        headers, body, status = grant.create_token_response(
            oauth_request, token_handler
        )
        assert headers == {
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Pragma": "no-cache",
        }
        assert body == json.dumps(
            {"error": "invalid_client", "error_description": "Client is invalid."}
        )
        assert status == 401

    def test_creates_token(self, grant, oauth_request, token_handler):
        grant.create_token_response(oauth_request, token_handler)

        token_handler.create_token.assert_called_once_with(
            oauth_request, refresh_token=True
        )

    def test_saves_token(self, grant, oauth_request, token_handler, request_validator):
        token = token_handler.create_token.return_value

        grant.create_token_response(oauth_request, token_handler)

        request_validator.save_token.assert_called_once_with(token, oauth_request)

    def test_returns_correct_headers(self, grant, oauth_request, token_handler):
        headers, _, _ = grant.create_token_response(oauth_request, token_handler)
        assert headers == {
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Pragma": "no-cache",
        }

    def test_returns_correct_body(self, grant, oauth_request, token_handler):
        _, body, _ = grant.create_token_response(oauth_request, token_handler)
        assert body == json.dumps(
            {
                "access_token": "test-access-token",
                "expires_in": 3600,
                "token_type": "Bearer",
            }
        )

    def test_returns_correct_status(self, grant, oauth_request, token_handler):
        _, _, status = grant.create_token_response(oauth_request, token_handler)

        assert status == 200

    @pytest.fixture
    def token_handler(self):
        handler = mock.Mock(spec_set=["create_token"])
        handler.create_token.return_value = {
            "access_token": "test-access-token",
            "expires_in": 3600,
            "token_type": "Bearer",
        }
        return handler


class TestJWTAuthorizationGrantValidateTokenRequest:
    def test_does_not_raise_for_valid_input(self, grant, oauth_request):
        grant.validate_token_request(oauth_request)

    def test_sets_client_id_from_token_on_request(
        self, grant, oauth_request, authclient
    ):
        assert oauth_request.client_id is None

        grant.validate_token_request(oauth_request)

        assert oauth_request.client_id == authclient.id

    def test_raises_for_missing_assertion(self, grant, oauth_request):
        del oauth_request._params["assertion"]  # pylint:disable=protected-access

        with pytest.raises(errors.InvalidRequestFatalError) as exc:
            grant.validate_token_request(oauth_request)

        assert exc.value.description == "Missing assertion."

    def test_raises_when_client_id_authentication_fails(
        self, grant, oauth_request, request_validator
    ):
        request_validator.authenticate_client_id.return_value = False

        with pytest.raises(errors.InvalidClientError):
            grant.validate_token_request(oauth_request)

    def test_validates_grant_type(self, grant, oauth_request, request_validator):
        request_validator.validate_grant_type.return_value = False

        with pytest.raises(errors.UnauthorizedClientError):
            grant.validate_token_request(oauth_request)

    def test_verifies_grant_token(self, grant, oauth_request):
        oauth_request.client.authclient.secret = "bogus"

        with pytest.raises(errors.InvalidGrantError) as exc:
            grant.validate_token_request(oauth_request)

        assert exc.value.description == "Invalid grant token signature."

    def test_sets_user_on_request(self, grant, oauth_request, user):
        assert oauth_request.user is None

        grant.validate_token_request(oauth_request)

        assert oauth_request.user == user

    def test_raises_when_user_cannot_be_found(
        self, grant, oauth_request, user, db_session
    ):
        db_session.delete(user)

        with pytest.raises(errors.InvalidGrantError) as exc:
            grant.validate_token_request(oauth_request)

        assert exc.value.description == "Grant token subject (sub) could not be found."

    def test_raises_when_user_authority_does_not_match_client_authority(
        self, grant, authclient, user
    ):
        user.authority = "bogus.org"
        oauth_request = _oauth_request(authclient, user)

        with pytest.raises(errors.InvalidGrantError) as exc:
            grant.validate_token_request(oauth_request)

        assert (
            exc.value.description
            == "Grant token subject (sub) does not match issuer (iss)."
        )


@pytest.fixture
def grant(pyramid_request, request_validator):
    user_svc = user_service_factory(None, pyramid_request)

    return JWTAuthorizationGrant(request_validator, user_svc, "domain.test")


def _oauth_request(authclient, user):
    exp = datetime.utcnow() + timedelta(minutes=5)
    nbf = datetime.utcnow() - timedelta(seconds=2)
    claims = {
        "aud": "domain.test",
        "exp": timegm(exp.utctimetuple()),
        "iss": authclient.id,
        "nbf": timegm(nbf.utctimetuple()),
        "sub": user.userid,
    }
    jwttok = jwt.encode(claims, authclient.secret, algorithm="HS256")

    return OAuthRequest("/", body={"assertion": jwttok, "client": Client(authclient)})


@pytest.fixture
def oauth_request(authclient, user):
    return _oauth_request(authclient, user)


@pytest.fixture
def authclient(factories):
    return factories.ConfidentialAuthClient()


@pytest.fixture
def user(factories, db_session):
    user = factories.User()
    db_session.flush()
    return user


@pytest.fixture
def request_validator():
    return mock.Mock()
