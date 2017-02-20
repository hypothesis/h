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

    def test_it_returns_the_user_and_authclient_from_the_jwt_token(self, svc, authclient, jwt_bearer_body, user):
        expected_user = user

        result = svc.verify_token_request(jwt_bearer_body)

        assert (expected_user, authclient) == result

    def test_missing_grant_type(self, svc, jwt_bearer_body):
        del jwt_bearer_body['grant_type']

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(jwt_bearer_body)

        assert exc.value.type == 'unsupported_grant_type'
        assert 'grant type is not supported' in exc.value.message

    def test_unsupported_grant_type(self, svc, jwt_bearer_body):
        jwt_bearer_body['grant_type'] = 'authorization_code'

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(jwt_bearer_body)

        assert exc.value.type == 'unsupported_grant_type'
        assert 'grant type is not supported' in exc.value.message

    def test_missing_assertion(self, svc, jwt_bearer_body):
        del jwt_bearer_body['assertion']

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(jwt_bearer_body)

        assert exc.value.type == 'invalid_request'
        assert 'assertion parameter is missing' in exc.value.message

    @pytest.mark.parametrize('assertion', [None, 57, '', 'bogus'])
    def test_non_jwt_assertion(self, svc, jwt_bearer_body, assertion):
        jwt_bearer_body['assertion'] = 'bogus'

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(jwt_bearer_body)

        assert exc.value.type == 'invalid_request'
        assert 'grant token format is invalid' in exc.value.message

    def test_missing_jwt_issuer(self, svc, claims, authclient, jwt_bearer_body):
        del claims['iss']
        jwt_bearer_body['assertion'] = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(jwt_bearer_body)

        assert exc.value.type == 'invalid_grant'
        assert 'issuer is missing' in exc.value.message

    def test_empty_jwt_issuer(self, svc, claims, authclient, jwt_bearer_body):
        claims['iss'] = ''
        jwt_bearer_body['assertion'] = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(jwt_bearer_body)

        assert exc.value.type == 'invalid_grant'
        assert 'issuer is missing' in exc.value.message

    def test_missing_authclient_with_given_jwt_issuer(self, svc, authclient, db_session, jwt_bearer_body):
        db_session.delete(authclient)
        db_session.flush()

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(jwt_bearer_body)

        assert exc.value.type == 'invalid_grant'
        assert 'issuer is invalid' in exc.value.message

    def test_non_uuid_jwt_issuer(self, svc, claims, authclient, jwt_bearer_body):
        claims['iss'] = 'bogus'
        jwt_bearer_body['assertion'] = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(jwt_bearer_body)

        assert exc.value.type == 'invalid_grant'
        assert 'issuer is invalid' in exc.value.message

    def test_signed_with_different_secret(self, svc, claims, jwt_bearer_body):
        jwt_bearer_body['assertion'] = self.jwt_token(claims, 'different-secret')

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(jwt_bearer_body)

        assert exc.value.type == 'invalid_grant'
        assert 'invalid JWT signature' in exc.value.message

    def test_signed_with_unsupported_algorithm(self, svc, claims, authclient, jwt_bearer_body):
        jwt_bearer_body['assertion'] = self.jwt_token(claims, authclient.secret, algorithm='HS512')

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(jwt_bearer_body)

        assert exc.value.type == 'invalid_grant'
        assert 'invalid JWT signature algorithm' in exc.value.message

    def test_missing_jwt_audience(self, svc, claims, authclient, jwt_bearer_body):
        del claims['aud']
        jwt_bearer_body['assertion'] = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(jwt_bearer_body)

        assert exc.value.type == 'invalid_grant'
        assert 'missing claim aud' in exc.value.message

    def test_invalid_jwt_audience(self, svc, claims, authclient, jwt_bearer_body):
        claims['aud'] = 'foobar.org'
        jwt_bearer_body['assertion'] = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(jwt_bearer_body)

        assert exc.value.type == 'invalid_grant'
        assert 'invalid JWT audience' in exc.value.message

    def test_jwt_not_before_in_future(self, svc, claims, authclient, jwt_bearer_body):
        claims['nbf'] = self.epoch(delta=timedelta(minutes=5))
        jwt_bearer_body['assertion'] = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(jwt_bearer_body)

        assert exc.value.type == 'invalid_grant'
        assert 'not before is in the future' in exc.value.message

    def test_jwt_expires_within_leeway(self, svc, claims, authclient, jwt_bearer_body):
        claims['exp'] = self.epoch(delta=timedelta(seconds=-8))
        jwt_bearer_body['assertion'] = self.jwt_token(claims, authclient.secret)

        svc.verify_token_request(jwt_bearer_body)

    def test_jwt_expires_with_leeway_in_the_past(self, svc, claims, authclient, jwt_bearer_body):
        claims['exp'] = self.epoch(delta=timedelta(minutes=-2))
        jwt_bearer_body['assertion'] = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(jwt_bearer_body)

        assert exc.value.type == 'invalid_grant'
        assert 'token is expired' in exc.value.message

    def test_jwt_issued_at_in_the_future(self, svc, claims, authclient, jwt_bearer_body):
        claims['iat'] = self.epoch(delta=timedelta(minutes=2))
        jwt_bearer_body['assertion'] = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(jwt_bearer_body)

        assert exc.value.type == 'invalid_grant'
        assert 'issued at is in the future' in exc.value.message

    def test_missing_jwt_subject(self, svc, claims, authclient, jwt_bearer_body):
        del claims['sub']
        jwt_bearer_body['assertion'] = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(jwt_bearer_body)

        assert exc.value.type == 'invalid_grant'
        assert 'subject is missing' in exc.value.message

    def test_empty_jwt_subject(self, svc, claims, authclient, jwt_bearer_body):
        claims['sub'] = ''
        jwt_bearer_body['assertion'] = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(jwt_bearer_body)

        assert exc.value.type == 'invalid_grant'
        assert 'subject is missing' in exc.value.message

    def test_user_not_found(self, svc, user_service, jwt_bearer_body):
        user_service.fetch.return_value = None

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(jwt_bearer_body)

        assert exc.value.type == 'invalid_grant'
        assert 'user with userid described in subject could not be found' in exc.value.message

    def test_it_raises_when_client_authority_does_not_match_userid(self, svc, db_session, user, jwt_bearer_body):
        user.authority = 'bogus-partner.org'
        db_session.flush()

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(jwt_bearer_body)

        assert exc.value.type == 'invalid_grant'
        assert 'authenticated client and JWT subject authorities do not match' in exc.value

    def test_missing_expiry(self, svc, claims, authclient, jwt_bearer_body):
        del claims['exp']
        jwt_bearer_body['assertion'] = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(jwt_bearer_body)

        assert exc.value.type == 'invalid_grant'
        assert 'JWT is missing claim exp' in exc.value

    def test_missing_nbf(self, svc, claims, authclient, jwt_bearer_body):
        del claims['nbf']
        jwt_bearer_body['assertion'] = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(jwt_bearer_body)

        assert exc.value.type == 'invalid_grant'
        assert 'JWT is missing claim nbf' in exc.value

    @pytest.mark.parametrize('claim_name', ['nbf', 'exp'])
    def test_null_timestamp(self, svc, claims, authclient, jwt_bearer_body, claim_name):
        claims[claim_name] = None
        jwt_bearer_body['assertion'] = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(jwt_bearer_body)

        assert exc.value.type == 'invalid_grant'
        assert 'JWT is missing claim {}'.format(claim_name) in exc.value

    @pytest.mark.parametrize('claim_name,delta',
                             [['nbf', timedelta(minutes=-5)],
                              ['exp', timedelta(minutes=5)]])
    def test_string_timestamp(self, svc, claims, authclient, jwt_bearer_body, claim_name, delta):
        claims[claim_name] = text_type(self.epoch(delta=delta))
        jwt_bearer_body['assertion'] = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(jwt_bearer_body)

        assert exc.value.type == 'invalid_grant'
        assert 'invalid claim {}'.format(claim_name) in exc.value

    @pytest.mark.parametrize('grant_start,grant_expiry',
                             [[None, timedelta(minutes=15)],
                              [timedelta(minutes=-15), None],
                              [timedelta(minutes=-9), timedelta(minutes=9)]])
    def test_overlong_expiry(self, svc, claims, authclient, jwt_bearer_body, grant_start, grant_expiry):
        claims['nbf'] = self.epoch(delta=grant_start)
        claims['exp'] = self.epoch(delta=grant_expiry)
        jwt_bearer_body['assertion'] = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(jwt_bearer_body)

        assert exc.value.type == 'invalid_grant'
        assert 'grant token lifetime is too long' in exc.value

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

    @pytest.fixture
    def jwt_bearer_body(self, claims, authclient):
        """
        Return the body of an OAuth jwt-bearer request.

        The JWT assertion in this request body contains the claims from
        the claims fixture (including the userid from the user fixture
        and the authclient from the authclient fixture) signed using the
        authclient secret from the authclient fixture.

        The request body also contains the correct grant_type for a
        jwt-bearer request.

        """
        return {
         'assertion': self.jwt_token(claims, authclient.secret),
         'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        }

    def jwt_token(self, claims, secret, algorithm='HS256'):
        return text_type(jwt.encode(claims, secret, algorithm=algorithm))

    def epoch(self, delta=None):
        timestamp = datetime.utcnow()

        if delta is not None:
            timestamp = timestamp + delta

        return timegm(timestamp.utctimetuple())


@pytest.mark.usefixtures('token')
class TestOAuthServiceVerifyRefreshTokenRequest(object):
    """Tests for verifying refresh token requests with OAuthService."""

    def test_it_raises_it_refresh_token_is_missing(self, refresh_token_body, svc):
        del refresh_token_body['refresh_token']

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(refresh_token_body)

        assert exc.value.type == 'invalid_request'
        assert 'refresh_token parameter is missing' in exc.value.message

    def test_it_raises_it_refresh_token_not_a_string(self, refresh_token_body, svc):
        refresh_token_body['refresh_token'] = 123

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(refresh_token_body)

        assert exc.value.type == 'invalid_refresh'
        assert 'refresh_token is invalid' in exc.value.message

    def test_it_raises_if_the_refresh_token_is_wrong(self, refresh_token_body, svc):
        """It raises if refresh_token doesn't match a token in the db."""
        refresh_token_body['refresh_token'] = 'wrong'

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(refresh_token_body)

        assert exc.value.type == 'invalid_refresh'
        assert 'refresh_token is invalid' in exc.value.message

    def test_it_raises_if_the_refresh_token_has_expired(self, refresh_token_body, svc, token):
        token.expires = datetime.utcnow() - timedelta(hours=1)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(refresh_token_body)

        assert exc.value.type == 'invalid_refresh'
        assert 'refresh_token has expired' in exc.value.message

    def test_it_raises_if_the_refresh_tokens_user_does_not_exist(self, refresh_token_body, svc, user_service):
        user_service.fetch.side_effect = lambda userid: None

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_token_request(refresh_token_body)

        assert exc.value.type == 'invalid_refresh'
        assert 'user no longer exists' in exc.value.message

    def test_it_fetches_the_user(self, refresh_token_body, svc, token, user_service):
        svc.verify_token_request(refresh_token_body)

        user_service.fetch.assert_called_once_with(token.userid)

    def test_it_returns_the_user(self, refresh_token_body, svc, user_service):
        user, _ = svc.verify_token_request(refresh_token_body)

        assert user == user_service.fetch.return_value

    def test_it_returns_the_authclient(self, refresh_token_body, svc, token):
        _, authclient = svc.verify_token_request(refresh_token_body)

        assert authclient == token.authclient

    @pytest.fixture
    def refresh_token(self):
        """The string value of the refresh_token used by these tests."""
        return 'foo'

    @pytest.fixture
    def refresh_token_body(self, refresh_token):
        """
        Return the body of an OAuth refresh_token request.

        The refresh_token in this request body is the same as that of the
        refresh_token fixture.

        The request body also contains the correct grant_type for a
        refresh_token request.

        """
        return {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }

    @pytest.fixture
    def svc(self, pyramid_request, db_session, user_service):
        return oauth.OAuthService(db_session, user_service, pyramid_request.domain)

    @pytest.fixture
    def token(self, factories, refresh_token):
        """
        Add a Token model to the database and return it.

        The token's refresh_token value is the same as the refresh_token
        fixture.

        """
        return factories.Token(refresh_token=refresh_token)

    @pytest.fixture
    def user(self, token):
        """A mock user whose userid is the same as the token fixture's userid."""
        return mock.Mock(spec_set=['userid'], userid=token.userid)

    @pytest.fixture
    def user_service(self, user, user_service):
        user_service.fetch.return_value = user
        return user_service


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
