# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from datetime import (datetime, timedelta)
from calendar import timegm

import jwt
import mock
import pytest

from h import models
from h.exceptions import OAuthTokenError
from h.services import oauth
from h.services.user import UserService
from h._compat import text_type


class TestOAuthServiceVerifyJWTBearerRequest(object):
    """Test for verifying jwt-bearer requests with OAuthService."""

    def test_it_returns_the_user_and_authclient_from_the_jwt_token(self, svc, claims, authclient, user):
        expected_user = user
        tok = self.jwt_token(claims, authclient.secret)

        result = svc.verify_token_request(dict(assertion=tok,
                                               grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer'))

        assert (expected_user, authclient) == result

    def test_missing_grant_type(self, svc):
        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(dict(assertion='jwt-token',
                                          grant_type=None))

        assert exc.value.type == 'unsupported_grant_type'
        assert 'grant type is not supported' in exc.value.message

    def test_unsupported_grant_type(self, svc):
        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(dict(assertion='jwt-token',
                                          grant_type='authorization_code'))

        assert exc.value.type == 'unsupported_grant_type'
        assert 'grant type is not supported' in exc.value.message

    def test_missing_assertion(self, svc):
        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(dict(assertion=None,
                                          grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer'))

        assert exc.value.type == 'invalid_request'
        assert 'assertion parameter is missing' in exc.value.message

    def test_non_jwt_assertion(self, svc):
        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(dict(assertion='bogus',
                                          grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer'))

        assert exc.value.type == 'invalid_grant'
        assert 'invalid JWT signature' in exc.value.message

    def test_missing_jwt_issuer(self, svc, claims, authclient):
        del claims['iss']
        tok = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(dict(assertion=tok,
                                          grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer'))

        assert exc.value.type == 'invalid_grant'
        assert 'issuer is missing' in exc.value.message

    def test_empty_jwt_issuer(self, svc, claims, authclient):
        claims['iss'] = ''
        tok = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(dict(assertion=tok,
                                          grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer'))

        assert exc.value.type == 'invalid_grant'
        assert 'issuer is missing' in exc.value.message

    def test_missing_authclient_with_given_jwt_issuer(self, svc, claims, authclient, db_session):
        db_session.delete(authclient)
        db_session.flush()

        tok = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(dict(assertion=tok,
                                          grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer'))

        assert exc.value.type == 'invalid_grant'
        assert 'issuer is invalid' in exc.value.message

    def test_non_uuid_jwt_issuer(self, svc, claims, authclient, db_session):
        claims['iss'] = 'bogus'
        tok = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(dict(assertion=tok,
                                          grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer'))

        assert exc.value.type == 'invalid_grant'
        assert 'issuer is invalid' in exc.value.message

    def test_signed_with_different_secret(self, svc, claims):
        tok = self.jwt_token(claims, 'different-secret')

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(dict(assertion=tok,
                                          grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer'))

        assert exc.value.type == 'invalid_grant'
        assert 'invalid JWT signature' in exc.value.message

    def test_signed_with_unsupported_algorithm(self, svc, claims, authclient):
        tok = self.jwt_token(claims, authclient.secret, algorithm='HS512')

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(dict(assertion=tok,
                                          grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer'))

        assert exc.value.type == 'invalid_grant'
        assert 'invalid JWT signature algorithm' in exc.value.message

    def test_missing_jwt_audience(self, svc, claims, authclient):
        del claims['aud']
        tok = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(dict(assertion=tok,
                                          grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer'))

        assert exc.value.type == 'invalid_grant'
        assert 'missing claim aud' in exc.value.message

    def test_invalid_jwt_audience(self, svc, claims, authclient):
        claims['aud'] = 'foobar.org'
        tok = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(dict(assertion=tok,
                                          grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer'))

        assert exc.value.type == 'invalid_grant'
        assert 'invalid JWT audience' in exc.value.message

    def test_jwt_not_before_in_future(self, svc, claims, authclient):
        claims['nbf'] = self.epoch(delta=timedelta(minutes=5))
        tok = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(dict(assertion=tok,
                                          grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer'))

        assert exc.value.type == 'invalid_grant'
        assert 'not before is in the future' in exc.value.message

    def test_jwt_expires_with_leeway_in_the_past(self, svc, claims, authclient):
        claims['exp'] = self.epoch(delta=timedelta(minutes=-2))
        tok = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(dict(assertion=tok,
                                          grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer'))

        assert exc.value.type == 'invalid_grant'
        assert 'token is expired' in exc.value.message

    def test_jwt_issued_at_in_the_future(self, svc, claims, authclient):
        claims['iat'] = self.epoch(delta=timedelta(minutes=2))
        tok = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(dict(assertion=tok,
                                          grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer'))

        assert exc.value.type == 'invalid_grant'
        assert 'issued at is in the future' in exc.value.message

    def test_missing_jwt_subject(self, svc, claims, authclient):
        del claims['sub']
        tok = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(dict(assertion=tok,
                                          grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer'))

        assert exc.value.type == 'invalid_grant'
        assert 'subject is missing' in exc.value.message

    def test_empty_jwt_subject(self, svc, claims, authclient):
        claims['sub'] = ''
        tok = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(dict(assertion=tok,
                                          grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer'))

        assert exc.value.type == 'invalid_grant'
        assert 'subject is missing' in exc.value.message

    def test_user_not_found(self, svc, claims, authclient, user_service):
        user_service.fetch.return_value = None

        tok = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(dict(assertion=tok,
                                          grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer'))

        assert exc.value.type == 'invalid_grant'
        assert 'user with userid described in subject could not be found' in exc.value.message

    def test_it_raises_when_client_authority_does_not_match_userid(self, svc, db_session, claims, authclient, user):
        user.authority = 'bogus-partner.org'
        db_session.flush()

        claims['sub'] = user.userid
        tok = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(dict(assertion=tok,
                                          grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer'))

        assert exc.value.type == 'invalid_grant'
        assert 'authenticated client and JWT subject authorities do not match' in exc.value

    @pytest.fixture
    def svc(self, pyramid_request, db_session, user_service):
        return oauth.OAuthService(db_session, user_service, pyramid_request.domain)

    @pytest.fixture
    def claims(self, authclient, user, pyramid_request):
        return {
            'iss': authclient.id,
            'sub': user.userid,
            'aud': pyramid_request.domain,
            'exp': self.epoch(delta=timedelta(minutes=10)),
            'nbf': self.epoch(),
            'iat': self.epoch(),
        }

    @pytest.fixture
    def authclient(self, db_session):
        client = models.AuthClient(authority='partner.org', secret='bogus')
        db_session.add(client)
        db_session.flush()
        return client

    @pytest.fixture
    def user(self, factories, authclient, user_service):
        user = factories.User.build(authority=authclient.authority)
        user_service.fetch.return_value = user
        return user

    def jwt_token(self, claims, secret, algorithm='HS256'):
        return text_type(jwt.encode(claims, secret, algorithm=algorithm))

    def epoch(self, timestamp=None, delta=None):
        if timestamp is None:
            timestamp = datetime.utcnow()

        if delta is not None:
            timestamp = timestamp + delta

        return timegm(timestamp.utctimetuple())


class TestOAuthServiceCreateToken(object):
    """ Tests for ``OAuthService.create_token`` """

    def test_it_creates_a_token(self, svc, user, authclient, db_session):
        query = db_session.query(models.Token).filter_by(userid=user.userid)

        assert query.count() == 0
        svc.create_token(user, authclient)
        assert query.count() == 1

    def test_it_returns_a_token(self, svc, user, authclient):
        token = svc.create_token(user, authclient)
        assert type(token) == models.Token

    def test_new_token_expires_within_one_hour(self, svc, db_session, user, authclient, utcnow):
        utcnow.return_value = datetime(2016, 1, 1, 3, 0, 0)

        svc.create_token(user, authclient)

        token = db_session.query(models.Token).filter_by(userid=user.userid).first()
        assert token.expires == datetime(2016, 1, 1, 4, 0, 0)

    def test_it_sets_the_passed_in_authclient(self, svc, user, authclient):
        token = svc.create_token(user, authclient)
        assert token.authclient == authclient

    @pytest.fixture
    def svc(self, pyramid_request, db_session, user_service):
        return oauth.OAuthService(db_session, user_service, pyramid_request.domain)

    @pytest.fixture
    def user(self, db_session, factories):
        user = factories.User()
        db_session.add(user)
        db_session.flush()
        return user

    @pytest.fixture
    def authclient(self, db_session):
        client = models.AuthClient(authority='partner.org', secret='bogus')
        db_session.add(client)
        db_session.flush()
        return client


@pytest.mark.usefixtures('user_service')
class TestOAuthServiceFactory(object):
    def test_it_returns_oauth_service(self, pyramid_request):
        svc = oauth.oauth_service_factory(None, pyramid_request)
        assert isinstance(svc, oauth.OAuthService)

    def test_it_provides_request_db_as_session(self, pyramid_request):
        svc = oauth.oauth_service_factory(None, pyramid_request)
        assert svc.session == pyramid_request.db

    def test_it_provides_user_service(self, pyramid_request, user_service):
        svc = oauth.oauth_service_factory(None, pyramid_request)
        assert svc.usersvc == user_service

    def test_it_provides_request_domain(self, pyramid_request):
        pyramid_request.domain = 'example.org'
        svc = oauth.oauth_service_factory(None, pyramid_request)
        assert svc.domain == 'example.org'


@pytest.fixture
def user_service(db_session, pyramid_config):
    service = mock.Mock(spec=UserService(default_authority='example.com',
                                         session=db_session))
    pyramid_config.register_service(service, name='user')
    return service


@pytest.fixture
def utcnow(patch):
    return patch('h.services.oauth.utcnow')
