# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime
import uuid

import mock
import pytest

from oauthlib.common import Request as OAuthRequest
from oauthlib.oauth2 import InvalidClientIdError

from h import models
from h._compat import text_type
from h.models.auth_client import GrantType as AuthClientGrantType
from h.models.auth_client import ResponseType as AuthClientResponseType
from h.services.oauth_validator import (
    OAuthValidatorService,
    oauth_validator_service_factory,
)


class TestAuthenticateClientId(object):
    def test_returns_true_when_client_found(self, svc, client, oauth_request):
        assert svc.authenticate_client_id(client.id, oauth_request) is True

    def test_sets_client_on_request_when_found(self, svc, client, oauth_request):
        assert oauth_request.client is None
        svc.authenticate_client_id(client.id, oauth_request)
        assert oauth_request.client == client

    def test_returns_false_when_client_missing(self, svc, oauth_request):
        assert svc.authenticate_client_id(text_type(uuid.uuid1()), oauth_request) is False

    @pytest.fixture
    def oauth_request(self):
        return OAuthRequest('/')


class TestFindClient(object):
    def test_returns_client(self, svc, client):
        assert svc.find_client(client.id) == client

    def test_returns_none_for_invalid_client_id(self, svc):
        assert svc.find_client('bogus') is None

    def test_returns_none_when_not_found(self, svc, client):
        id_ = text_type(uuid.uuid1())
        assert svc.find_client(id_) is None


class TestGetDefaultRedirectUri(object):
    def test_returns_clients_redirect_uri(self, svc, client):
        actual = svc.get_default_redirect_uri(client.id, None)
        assert 'https://example.org/auth/callback' == actual

    def test_returns_none_when_client_missing(self, svc):
        id_ = text_type(uuid.uuid1())
        assert svc.get_default_redirect_uri(id_, None) is None

    @pytest.fixture
    def client(self, factories):
        redirect_uri = 'https://example.org/auth/callback'
        return factories.AuthClient(redirect_uri=redirect_uri)


class TestGetDefaultScopes(object):
    def test_returns_default_scopes(self, svc):
        assert svc.get_default_scopes('something', None) == [
            'annotation:read', 'annotation:write']


class TestSaveAuthorizationCode(object):
    def test_it_raises_for_missing_client(self, svc, code, oauth_request):
        id_ = text_type(uuid.uuid1())
        with pytest.raises(InvalidClientIdError):
            svc.save_authorization_code(id_, code, oauth_request)

    def test_it_saves_authz_code(self, db_session, svc, client, code, oauth_request):
        assert db_session.query(models.AuthzCode).count() == 0
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
        assert authz_code.code == 'abcdef123456'

    @pytest.fixture
    def code(self):
        return {'code': 'abcdef123456'}

    @pytest.fixture
    def oauth_request(self, factories):
        return mock.Mock(user=factories.User(), spec_set=['user'])


class TestSaveBearerToken(object):
    def test_it_saves_token(self, svc, db_session, token_payload, oauth_request):
        assert db_session.query(models.Token).count() == 0
        svc.save_bearer_token(token_payload, oauth_request)
        assert db_session.query(models.Token).count() == 1

    def test_it_sets_userid(self, svc, token_payload, oauth_request):
        token = svc.save_bearer_token(token_payload, oauth_request)
        assert token.userid == oauth_request.user.userid

    def test_it_sets_value(self, svc, token_payload, oauth_request):
        token = svc.save_bearer_token(token_payload, oauth_request)
        assert token.value == 'test-access-token'

    def test_it_sets_expires(self, svc, token_payload, oauth_request, utcnow):
        utcnow.return_value = datetime.datetime(2017, 7, 13, 18, 29, 28)

        token = svc.save_bearer_token(token_payload, oauth_request)
        assert token.expires == datetime.datetime(2017, 7, 13, 19, 29, 28)

    def test_it_sets_authclient(self, svc, token_payload, oauth_request):
        token = svc.save_bearer_token(token_payload, oauth_request)
        assert token.refresh_token == 'test-refresh-token'

    @pytest.fixture
    def oauth_request(self, factories):
        return OAuthRequest('/', body={'user': factories.User()})

    @pytest.fixture
    def token_payload(self):
        return {
            'access_token': 'test-access-token',
            'refresh_token': 'test-refresh-token',
            'expires_in': 3600,
        }


class TestValidateClientId(object):
    def test_returns_true_for_valid_client(self, svc, client):
        assert svc.validate_client_id(client.id, None) is True

    def test_returns_false_for_missing_client(self, svc):
        id_ = text_type(uuid.uuid1())
        assert svc.validate_client_id(id_, None) is False


class TestValidateGrantType(object):
    def test_returns_false_when_client_does_not_have_grant_types(self, svc, client, oauth_request):
        client.grant_type = None

        result = svc.validate_grant_type(client.id, 'authorization_code', client, oauth_request)
        assert result is False

    def test_returns_true_when_grant_type_matches_client(self, svc, client, oauth_request):
        client.grant_type = AuthClientGrantType.authorization_code

        result = svc.validate_grant_type(client.id, 'authorization_code', client, oauth_request)
        assert result is True

    def test_returns_false_when_grant_type_does_not_match_client(self, svc, client, oauth_request):
        client.grant_type = AuthClientGrantType.client_credentials

        result = svc.validate_grant_type(client.id, 'authorization_code', client, oauth_request)
        assert result is False

    @pytest.fixture
    def oauth_request(self):
        return OAuthRequest('/')


class TestValidateRedirectUri(object):
    def test_returns_true_for_valid_redirect_uri(self, svc, client):
        redirect_uri = 'https://example.org/auth/callback'
        actual = svc.validate_redirect_uri(client.id, redirect_uri, None)
        assert actual is True

    def test_returns_false_for_invalid_redirect_uri(self, svc, client):
        redirect_uri = 'https://example.com'
        actual = svc.validate_redirect_uri(client.id, redirect_uri, None)
        assert actual is False

    def test_returns_false_for_missing_clint(self, svc):
        redirect_uri = 'https://example.com'
        actual = svc.validate_redirect_uri('something', redirect_uri, None)
        assert actual is False

    @pytest.fixture
    def client(self, factories):
        redirect_uri = 'https://example.org/auth/callback'
        return factories.AuthClient(redirect_uri=redirect_uri)


class TestValidateResponseType(object):
    def test_returns_true_when_matching(self, svc, client):
        actual = svc.validate_response_type(client.id, 'code', None)
        assert actual is True

    def test_returns_false_when_not_matchind(self, svc, client):
        actual = svc.validate_response_type(client.id, 'token', None)
        assert actual is False

    def test_returns_false_for_missing_client(self, svc):
        id_ = text_type(uuid.uuid1())
        assert svc.validate_response_type(id_, 'code', None) is False

    @pytest.fixture
    def client(self, factories):
        return factories.AuthClient(response_type=AuthClientResponseType.code)


class TestValidateScopes(object):
    def test_returns_true_for_default_scopes(self, svc):
        scopes = svc.get_default_scopes('something', None)
        assert svc.validate_scopes('something', scopes, None) is True

    def test_returns_false_for_other_scopes(self, svc):
        scopes = ['user:delete']
        assert svc.validate_scopes('something', scopes, None) is False

    def test_returns_false_for_empty_scopes(self, svc):
        scopes = []
        assert svc.validate_scopes('something', scopes, None) is False

    def test_returns_false_for_none_scopes(self, svc):
        scopes = None
        assert svc.validate_scopes('something', scopes, None) is False


class TestOAuthValidatorServiceFactory(object):
    def test_it_returns_oauth_service(self, pyramid_request):
        svc = oauth_validator_service_factory(None, pyramid_request)
        assert isinstance(svc, OAuthValidatorService)


@pytest.fixture
def svc(db_session):
    return OAuthValidatorService(db_session)


@pytest.fixture
def client(factories):
    return factories.AuthClient()


@pytest.fixture
def utcnow(patch):
    return patch('h.services.oauth_validator.utcnow')
