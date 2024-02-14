import datetime
import uuid
from unittest import mock

import pytest
from oauthlib.common import Request as OAuthRequest
from oauthlib.oauth2 import InvalidClientIdError

from h import models
from h.models.auth_client import GrantType as AuthClientGrantType
from h.models.auth_client import ResponseType as AuthClientResponseType
from h.services.oauth._validator import Client, OAuthValidator


class TestAuthenticateClient:
    def test_returns_True_when_client_secret_matches_request(
        self, svc, client, oauth_request
    ):
        oauth_request.client_id = client.id
        oauth_request.client_secret = client.secret

        assert svc.authenticate_client(oauth_request) is True

    def test_sets_client_on_request_when_authentication_succeded(
        self, svc, client, oauth_request
    ):
        oauth_request.client_id = client.id
        oauth_request.client_secret = client.secret

        svc.authenticate_client(oauth_request)
        assert oauth_request.client.client_id == client.id
        assert oauth_request.client.authclient == client

    def test_returns_False_for_missing_client_id_request_param(
        self, svc, oauth_request
    ):
        assert not svc.authenticate_client(oauth_request)

    def test_returns_False_for_missing_client_secret_request_param(
        self, svc, client, oauth_request
    ):
        oauth_request.client_id = client.id
        assert not svc.authenticate_client(oauth_request)

    def test_returns_False_for_missing_client(self, svc, client, oauth_request):
        oauth_request.client_id = uuid.uuid1()
        oauth_request.client_secret = client.secret

        assert not svc.authenticate_client(oauth_request)

    def test_returns_False_when_secrets_do_not_match(self, svc, client, oauth_request):
        oauth_request.client_id = client.id
        oauth_request.client_secret = "this-is-invalid"

        assert not svc.authenticate_client(oauth_request)

    @pytest.fixture
    def client(self, factories):
        return factories.ConfidentialAuthClient()


class TestAuthenticateClientId:
    def test_returns_True_when_client_found(self, svc, client, oauth_request):
        assert svc.authenticate_client_id(client.id, oauth_request) is True

    def test_sets_client_on_request_when_found(self, svc, client, oauth_request):
        assert oauth_request.client is None
        svc.authenticate_client_id(client.id, oauth_request)
        assert oauth_request.client.client_id == client.id
        assert oauth_request.client.authclient == client

    def test_returns_False_when_client_missing(self, svc, oauth_request):
        assert not svc.authenticate_client_id(str(uuid.uuid1()), oauth_request)


class TestClientAuthenticationRequired:
    def test_returns_False_for_public_client(self, svc, oauth_request, factories):
        client = factories.AuthClient()
        oauth_request.client_id = client.id
        assert not svc.client_authentication_required(oauth_request)

    def test_returns_True_for_confidential_client(self, svc, oauth_request, factories):
        client = factories.ConfidentialAuthClient()
        oauth_request.client_id = client.id
        assert svc.client_authentication_required(oauth_request) is True

    def test_returns_False_for_missing_client(self, svc, oauth_request):
        oauth_request.client = None
        assert not svc.client_authentication_required(oauth_request)

    def test_returns_False_for_refresh_token_with_jwt_client(
        self, svc, oauth_request, client
    ):
        oauth_request.client_id = client.id
        oauth_request.grant_type = "refresh_token"
        assert not svc.client_authentication_required(oauth_request)

    def test_returns_False_for_revoke_token(self, svc, oauth_request, client):
        oauth_request.client_id = client.id
        oauth_request.h_revoke_request = True

        assert not svc.client_authentication_required(oauth_request)

    @pytest.fixture
    def client(self, factories):
        return factories.ConfidentialAuthClient(
            grant_type=AuthClientGrantType.jwt_bearer
        )

    @pytest.fixture
    def oauth_request(self):
        return OAuthRequest("/", body={"grant_type": "authorization_code"})


class TestConfirmRedirectUri:
    @pytest.mark.parametrize(
        "db_uri,redirect_uri",
        (
            ("{current_scheme}://{current_host}/abcd", "https://example.com/abcd"),
            ("{current_scheme}://{current_host}/abcd", "ftps://example.co.uk/abcd"),
            ("http://example.com/abcd", "http://example.com/abcd"),
        ),
    )
    def test_returns_True_for_matching_uris(self, svc, client, db_uri, redirect_uri):
        client.authclient.redirect_uri = db_uri
        result = svc.confirm_redirect_uri(
            client.client_id, "test-authz-code", redirect_uri, client
        )
        assert result is True

    @pytest.mark.parametrize(
        "db_uri,redirect_uri",
        [
            ("{current_scheme}://{current_host}/abcd", "https://example.com/bad_path"),
            ("http://example.com/abcd", "https://different.com/abcd"),
        ],
    )
    def test_returns_False_when_templated_uris_do_not_match(
        self, svc, client, db_uri, redirect_uri
    ):
        client.authclient.redirect_uri = db_uri
        result = svc.confirm_redirect_uri(
            client.client_id, "test-authz-code", redirect_uri, client
        )
        assert not result

    def test_returns_True_when_redirect_uri_not_provided(self, svc, client):
        result = svc.confirm_redirect_uri(
            client.client_id, "test-authz-code", None, client
        )
        assert result is True

    @pytest.fixture
    def client(self, factories):
        return Client(factories.AuthClient())


class TestFindAuthzCode:
    def test_returns_authz_code(self, svc, authz_code):
        assert svc.find_authz_code(authz_code.code) == authz_code

    def test_returns_none_when_not_found(self, svc):
        assert svc.find_authz_code("missing") is None

    def test_returns_none_for_none_code(self, svc):
        assert svc.find_authz_code(None) is None

    @pytest.fixture
    def authz_code(self, factories):
        return factories.AuthzCode()


class TestFindClient:
    def test_returns_client(self, svc, client):
        assert svc.find_client(client.id) == client

    def test_returns_none_for_invalid_client_id(self, svc):
        assert svc.find_client("bogus") is None

    def test_returns_none_when_not_found(self, svc):
        id_ = str(uuid.uuid1())
        assert svc.find_client(id_) is None

    def test_returns_none_when_id_none(self, svc):
        assert svc.find_client(None) is None


class TestFindRefreshToken:
    def test_returns_token(self, svc, token):
        assert svc.find_refresh_token(token.refresh_token) == token

    def test_returns_none_when_not_found(self, svc):
        assert svc.find_refresh_token("missing") is None

    @pytest.fixture
    def token(self, factories):
        return factories.OAuth2Token()


class TestGetDefaultRedirectUri:
    def test_returns_clients_redirect_uri(self, svc, client):
        actual = svc.get_default_redirect_uri(
            client.id, OAuthRequest("ftps://example.org")
        )

        assert actual == "ftps://example.org/auth/callback"

    def test_returns_none_when_client_missing(self, svc):
        id_ = str(uuid.uuid1())
        assert svc.get_default_redirect_uri(id_, None) is None

    @pytest.fixture
    def client(self, factories):
        redirect_uri = "{current_scheme}://{current_host}/auth/callback"
        return factories.AuthClient(redirect_uri=redirect_uri)


class TestGetDefaultScopes:
    def test_returns_default_scopes(self, svc):
        assert svc.get_default_scopes("something", None) == [
            "annotation:read",
            "annotation:write",
        ]


class TestGetOriginalScopes:
    def test_returns_original_scopes_from_default_ones(self, svc):
        refresh_token = mock.Mock()
        oauth_request = mock.Mock()
        assert svc.get_original_scopes(
            refresh_token, oauth_request
        ) == svc.get_default_scopes("something", oauth_request)


class TestInvalidateAuthorizationCode:
    def test_it_deletes_authz_code(self, svc, oauth_request, factories, db_session):
        authz_code_1 = factories.AuthzCode()
        id_1 = authz_code_1.id
        authz_code_2 = factories.AuthzCode(authclient=authz_code_1.authclient)
        id_2 = authz_code_2.id

        svc.invalidate_authorization_code(
            authz_code_1.authclient.id, authz_code_1.code, oauth_request
        )
        db_session.flush()

        assert db_session.get(models.AuthzCode, id_1) is None
        assert db_session.get(models.AuthzCode, id_2) is not None

    def test_it_skips_deleting_when_authz_code_is_missing(
        self, svc, oauth_request, db_session, factories
    ):
        keep_code = factories.AuthzCode()

        svc.invalidate_authorization_code(
            keep_code.authclient.id, "missing", oauth_request
        )
        db_session.flush()

        assert db_session.get(models.AuthzCode, keep_code.id) is not None


class TestFindToken:
    def test_it_can_get_token_by_refresh_value(self, svc, token):
        token = svc.find_token(token.refresh_token)

        assert token.refresh_token == token.refresh_token

    def test_it_can_get_token_by_value(self, svc, token):
        token = svc.find_token(token.value)

        assert token.value == token.value

    def test_it_returns_None_when_token_is_missing(self, svc):
        result = svc.find_token("missing-value")

        assert result is None

    @pytest.fixture
    def token(self, factories):
        return factories.OAuth2Token()


class TestInvalidateRefreshToken:
    def test_it_shortens_refresh_token_expires(self, svc, oauth_request, token, utcnow):
        utcnow.return_value = datetime.datetime(2017, 8, 2, 18, 36, 53)

        svc.invalidate_refresh_token(token.refresh_token, oauth_request)
        assert token.refresh_token_expires == datetime.datetime(2017, 8, 2, 18, 39, 53)

    def test_it_is_noop_when_refresh_token_expires_within_new_ttl(
        self, svc, oauth_request, token, utcnow
    ):
        utcnow.return_value = datetime.datetime(2017, 8, 2, 18, 36, 53)
        token.refresh_token_expires = datetime.datetime(2017, 8, 2, 18, 37, 53)

        svc.invalidate_refresh_token(token.refresh_token, oauth_request)
        assert token.refresh_token_expires == datetime.datetime(2017, 8, 2, 18, 37, 53)

    @pytest.fixture
    def token(self, factories):
        return factories.OAuth2Token()


class TestRevokeToken:
    def test_it_deletes_token_when_access_token(
        self, svc, factories, db_session, oauth_request
    ):
        token = factories.OAuth2Token()
        assert db_session.query(models.Token).count() == 1

        svc.revoke_token(token.value, None, oauth_request)
        assert not db_session.query(models.Token).count()

    def test_it_deletes_token_when_refresh_token(
        self, svc, factories, db_session, oauth_request
    ):
        token = factories.OAuth2Token()
        assert db_session.query(models.Token).count() == 1

        svc.revoke_token(token.refresh_token, None, oauth_request)
        assert not db_session.query(models.Token).count()

    def test_it_ignores_other_tokens(self, svc, factories, db_session, oauth_request):
        token = factories.DeveloperToken()
        assert db_session.query(models.Token).count() == 1

        svc.revoke_token(token.value, None, oauth_request)
        assert db_session.query(models.Token).count() == 1

    def test_it_is_noop_when_token_is_missing(
        self, svc, factories, db_session, oauth_request
    ):
        token = factories.OAuth2Token()
        tok = token.value
        db_session.delete(token)

        svc.revoke_token(tok, None, oauth_request)


class TestSaveAuthorizationCode:
    def test_it_raises_for_missing_client(self, svc, code, oauth_request):
        id_ = str(uuid.uuid1())
        with pytest.raises(InvalidClientIdError):
            svc.save_authorization_code(id_, code, oauth_request)

    def test_it_saves_authz_code(self, db_session, svc, client, code, oauth_request):
        assert not db_session.query(models.AuthzCode).count()
        svc.save_authorization_code(client.id, code, oauth_request)
        assert db_session.query(models.AuthzCode).count() == 1

    def test_it_sets_user(self, svc, client, code, oauth_request):
        authz_code = svc.save_authorization_code(client.id, code, oauth_request)
        assert authz_code.user == oauth_request.user

    def test_it_sets_authclient(self, svc, client, code, oauth_request):
        authz_code = svc.save_authorization_code(client.id, code, oauth_request)
        assert authz_code.authclient == client

    def test_it_sets_expires(self, svc, client, code, oauth_request, utcnow):
        utcnow.return_value = datetime.datetime(2017, 7, 13, 18, 29, 28)

        authz_code = svc.save_authorization_code(client.id, code, oauth_request)
        assert authz_code.expires == datetime.datetime(2017, 7, 13, 18, 39, 28)

    def test_it_sets_code(self, svc, client, code, oauth_request):
        authz_code = svc.save_authorization_code(client.id, code, oauth_request)
        assert authz_code.code == "abcdef123456"

    @pytest.fixture
    def code(self):
        return {"code": "abcdef123456"}

    @pytest.fixture
    def oauth_request(self, factories):
        return mock.Mock(user=factories.User(), spec_set=["user"])


class TestSaveBearerToken:
    def test_it_saves_token(self, svc, db_session, token_payload, oauth_request):
        assert not db_session.query(models.Token).count()
        svc.save_bearer_token(token_payload, oauth_request)
        assert db_session.query(models.Token).count() == 1

    def test_it_sets_userid(self, svc, token_payload, oauth_request):
        token = svc.save_bearer_token(token_payload, oauth_request)
        assert token.user == oauth_request.user

    def test_it_sets_value(self, svc, token_payload, oauth_request):
        token = svc.save_bearer_token(token_payload, oauth_request)
        assert token.value == "test-access-token"

    def test_it_sets_expires(self, svc, token_payload, oauth_request, utcnow):
        utcnow.return_value = datetime.datetime(2017, 7, 13, 18, 29, 28)

        token = svc.save_bearer_token(token_payload, oauth_request)
        assert token.expires == datetime.datetime(2017, 7, 13, 19, 29, 28)

    def test_it_sets_refresh_token_expires(
        self, svc, token_payload, oauth_request, utcnow
    ):
        utcnow.return_value = datetime.datetime(2017, 7, 13, 18, 29, 28)

        token = svc.save_bearer_token(token_payload, oauth_request)
        assert token.refresh_token_expires == datetime.datetime(2017, 7, 13, 20, 29, 28)

    def test_it_sets_authclient(self, svc, token_payload, oauth_request):
        token = svc.save_bearer_token(token_payload, oauth_request)
        assert token.refresh_token == "test-refresh-token"

    def test_it_removes_refresh_token_expires_in_from_payload(
        self, svc, token_payload, oauth_request
    ):
        assert "refresh_token_expires_in" in token_payload
        svc.save_bearer_token(token_payload, oauth_request)
        assert "refresh_token_expires_in" not in token_payload

    def test_it_invalidates_old_refresh_token(
        self, svc, token_payload, oauth_request, patch
    ):
        invalidate_refresh_token = patch(
            "h.services.oauth._validator.OAuthValidator.invalidate_refresh_token"
        )
        oauth_request.grant_type = "refresh_token"
        oauth_request.refresh_token = "the-refresh-token"

        svc.save_bearer_token(token_payload, oauth_request)

        invalidate_refresh_token.assert_called_once_with(
            svc, "the-refresh-token", oauth_request
        )

    def test_it_skips_invalidating_old_refresh_token_when_not_refresh_grant(
        self, svc, token_payload, oauth_request, patch
    ):
        invalidate_refresh_token = patch(
            "h.services.oauth._validator.OAuthValidator.invalidate_refresh_token"
        )

        svc.save_bearer_token(token_payload, oauth_request)

        assert not invalidate_refresh_token.called

    @pytest.fixture
    def oauth_request(self, factories):
        return OAuthRequest(
            "/",
            body={"user": factories.User(), "client": Client(factories.AuthClient())},
        )

    @pytest.fixture
    def token_payload(self):
        return {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "expires_in": 3600,
            "refresh_token_expires_in": 7200,
        }


class TestValidateClientId:
    def test_returns_True_for_valid_client(self, svc, client):
        assert svc.validate_client_id(client.id, None) is True

    def test_returns_False_for_missing_client(self, svc):
        id_ = str(uuid.uuid1())
        assert not svc.validate_client_id(id_, None)


class TestValidateCode:
    def test_returns_True_for_correct_code(
        self, svc, authz_code, client, oauth_request
    ):
        result = svc.validate_code(
            client.client_id, authz_code.code, client, oauth_request
        )
        assert result is True

    def test_sets_user_on_request(self, svc, authz_code, client, oauth_request):
        assert oauth_request.user is None
        svc.validate_code(client.client_id, authz_code.code, client, oauth_request)
        assert oauth_request.user == authz_code.user

    def test_sets_scopes_on_request(self, svc, authz_code, client, oauth_request):
        assert oauth_request.scopes is None
        svc.validate_code(client.client_id, authz_code.code, client, oauth_request)
        assert oauth_request.scopes == svc.get_default_scopes(
            client.client_id, oauth_request
        )

    def test_returns_False_for_missing_code(self, svc, client, oauth_request):
        result = svc.validate_code(client.client_id, "missing", client, oauth_request)
        assert not result

    def test_returns_False_when_clients_do_not_match(
        self, svc, client, oauth_request, factories
    ):
        authz_code = factories.AuthzCode()
        result = svc.validate_code(
            client.client_id, authz_code.code, client, oauth_request
        )
        assert not result

    def test_returns_False_when_expired(self, svc, authz_code, client, oauth_request):
        authz_code.expires = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)

        result = svc.validate_code(
            client.client_id, authz_code.code, client, oauth_request
        )
        assert not result

    @pytest.fixture
    def authz_code(self, factories, client):
        return factories.AuthzCode(authclient=client.authclient)

    @pytest.fixture
    def client(self, factories):
        return Client(factories.AuthClient())


class TestValidateGrantType:
    def test_returns_False_when_client_does_not_have_grant_types(
        self, svc, client, oauth_request
    ):
        client.authclient.grant_type = None

        result = svc.validate_grant_type(
            client.client_id, "authorization_code", client, oauth_request
        )
        assert not result

    def test_returns_True_when_grant_type_matches_client(
        self, svc, client, oauth_request
    ):
        client.authclient.grant_type = AuthClientGrantType.authorization_code

        result = svc.validate_grant_type(
            client.client_id, "authorization_code", client, oauth_request
        )
        assert result is True

    def test_returns_True_when_refresh_token_and_client_does_not_match(
        self, svc, client, oauth_request
    ):
        client.authclient.grant_type = AuthClientGrantType.authorization_code

        result = svc.validate_grant_type(
            client.client_id, "refresh_token", client, oauth_request
        )
        assert result is True

    def test_returns_False_when_grant_type_does_not_match_client(
        self, svc, client, oauth_request
    ):
        client.authclient.grant_type = AuthClientGrantType.client_credentials

        result = svc.validate_grant_type(
            client.client_id, "authorization_code", client, oauth_request
        )
        assert not result

    @pytest.fixture
    def client(self, factories):
        return Client(factories.AuthClient())


class TestValidateRedirectUri:
    @pytest.mark.parametrize(
        "db_uri,redirect_uri",
        (
            ("{current_scheme}://{current_host}/abcd", "https://example.com/abcd"),
            ("{current_scheme}://{current_host}/abcd", "ftps://example.co.uk/abcd"),
            ("http://example.com/abcd", "http://example.com/abcd"),
        ),
    )
    def test_returns_True_for_valid_redirect_uri(
        self, svc, client, db_uri, redirect_uri
    ):
        client.redirect_uri = db_uri
        actual = svc.validate_redirect_uri(client.id, redirect_uri, None)
        assert actual is True

    @pytest.mark.parametrize(
        "db_uri,redirect_uri",
        [
            ("{current_scheme}://{current_host}/abcd", "https://example.com/bad_path"),
            ("http://example.com/abcd", "https://different.com/abcd"),
        ],
    )
    def test_returns_False_for_invalid_redirect_uri(
        self, svc, client, db_uri, redirect_uri
    ):
        client.redirect_uri = db_uri
        actual = svc.validate_redirect_uri(client.id, redirect_uri, None)
        assert not actual

    def test_returns_False_for_missing_client(self, svc):
        redirect_uri = "https://example.com"
        actual = svc.validate_redirect_uri("something", redirect_uri, None)
        assert not actual

    @pytest.fixture
    def client(self, factories):
        return factories.AuthClient()


class TestValidateRefreshToken:
    def test_returns_False_when_token_not_found(self, svc, client, oauth_request):
        result = svc.validate_refresh_token("missing", client, oauth_request)
        assert not result

    def test_returns_False_when_refresh_token_expired(
        self, svc, client, oauth_request, token
    ):
        token.refresh_token_expires = datetime.datetime.utcnow() - datetime.timedelta(
            minutes=2
        )
        result = svc.validate_refresh_token(token.refresh_token, client, oauth_request)
        assert not result

    def test_returns_False_when_token_client_does_not_match_request_client(
        self, svc, oauth_request, token, factories
    ):
        request_client = Client(factories.AuthClient())
        result = svc.validate_refresh_token(
            token.refresh_token, request_client, oauth_request
        )
        assert not result

    def test_returns_True_when_token_valid(self, svc, client, oauth_request, token):
        result = svc.validate_refresh_token(token.refresh_token, client, oauth_request)
        assert result is True

    def test_returns_True_when_access_token_expired(
        self, svc, client, oauth_request, token
    ):
        token.expires = datetime.datetime.utcnow() - datetime.timedelta(minutes=2)
        result = svc.validate_refresh_token(token.refresh_token, client, oauth_request)
        assert result is True

    def test_sets_user_when_token_valid(self, svc, client, oauth_request, token):
        assert oauth_request.user is None

        svc.validate_refresh_token(token.refresh_token, client, oauth_request)

        assert oauth_request.user == token.user

    @pytest.fixture
    def token(self, factories, client):
        return factories.OAuth2Token(authclient=client.authclient)

    @pytest.fixture
    def client(self, factories):
        return Client(factories.AuthClient())


class TestValidateResponseType:
    def test_returns_True_when_matching(self, svc, client):
        actual = svc.validate_response_type(client.id, "code", None)
        assert actual is True

    def test_returns_False_when_not_matchind(self, svc, client):
        actual = svc.validate_response_type(client.id, "token", None)
        assert not actual

    def test_returns_False_for_missing_client(self, svc):
        id_ = str(uuid.uuid1())
        assert not svc.validate_response_type(id_, "code", None)

    def test_returns_False_for_missing_client_response_type(self, svc, client):
        client.response_type = None

        actual = svc.validate_response_type(client.id, "code", None)
        assert not actual

    @pytest.fixture
    def client(self, factories):
        return factories.AuthClient(response_type=AuthClientResponseType.code)


class TestValidateScopes:
    def test_returns_True_for_default_scopes(self, svc):
        scopes = svc.get_default_scopes("something", None)
        assert svc.validate_scopes("something", scopes, None) is True

    def test_returns_False_for_other_scopes(self, svc):
        scopes = ["user:delete"]
        assert not svc.validate_scopes("something", scopes, None)

    def test_returns_False_for_empty_scopes(self, svc):
        scopes = []
        assert not svc.validate_scopes("something", scopes, None)

    def test_returns_False_for_none_scopes(self, svc):
        scopes = None
        assert not svc.validate_scopes("something", scopes, None)


@pytest.fixture
def svc(db_session):
    return OAuthValidator(db_session)


@pytest.fixture
def oauth_request():
    return OAuthRequest("/")


@pytest.fixture
def client(factories):
    return factories.AuthClient()


@pytest.fixture
def utcnow(patch):
    return patch("h.services.oauth._validator.utcnow")
