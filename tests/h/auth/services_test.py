# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from datetime import (datetime, timedelta)
from calendar import timegm

import jwt
import mock
import pytest

from h import models
from h.services.user import UserService
from h.auth import services
from h.exceptions import OAuthTokenError
from h._compat import text_type


class TestAuthTicketService(object):
    def test_userid_raises_when_ticket_has_not_been_loaded_yet(self, svc):
        with pytest.raises(services.AuthTicketNotLoadedError) as exc:
            svc.userid()
        assert str(exc.value) == 'auth ticket is not loaded yet'

    def test_userid_returns_the_users_userid(self, svc, ticket):
        svc.usersvc.fetch.return_value = ticket.user

        svc.verify_ticket(ticket.user_userid, ticket.id)

        userid = svc.userid()
        assert ticket.user.userid == userid

    @pytest.mark.usefixtures('principals_for_user')
    def test_groups_loads_the_user(self, svc, ticket):
        svc.verify_ticket(ticket.user_userid, ticket.id)

        svc.groups()

        assert svc.usersvc.fetch.call_count == 1
        svc.usersvc.fetch.assert_called_once_with(ticket.user_userid)

    def test_groups_returns_principals_for_user(self, svc, principals_for_user, ticket):
        principals_for_user.return_value = ['foo', 'bar', 'baz']
        svc.usersvc.fetch.return_value = ticket.user
        svc.verify_ticket(ticket.user_userid, ticket.id)

        result = svc.groups()

        principals_for_user.assert_called_once_with(ticket.user)
        assert ['foo', 'bar', 'baz'] == result

    def test_groups_raises_when_ticket_is_not_loaded(self, svc, ticket):
        with pytest.raises(services.AuthTicketNotLoadedError) as exc:
            svc.groups()
        assert str(exc.value) == 'auth ticket is not loaded yet'

    def test_verify_ticket_fails_when_id_is_None(self, svc):
        assert svc.verify_ticket(self.principal, None) is False

    def test_verify_ticket_fails_when_id_is_empty(self, svc):
        assert svc.verify_ticket(self.principal, '') is False

    @pytest.mark.usefixtures('ticket')
    def test_verify_ticket_fails_when_ticket_cannot_be_found(self, svc, db_session):
        assert svc.verify_ticket('foobar', 'bogus') is False

    def test_verify_ticket_fails_when_ticket_user_does_not_match_principal(self, svc, db_session, ticket):
        assert svc.verify_ticket('foobar', ticket.id) is False

    def test_verify_ticket_fails_when_ticket_is_expired(self, svc, db_session, factories):
        expires = datetime.utcnow() - timedelta(hours=3)
        ticket = factories.AuthTicket(expires=expires)
        db_session.flush()

        assert svc.verify_ticket(ticket.user_userid, ticket.id) is False

    def test_verify_ticket_succeeds_when_ticket_is_valid(self, svc, db_session, ticket):
        assert svc.verify_ticket(ticket.user_userid, ticket.id) is True

    def test_verify_ticket_skips_extending_expiration_when_within_refresh_interval(self, svc, db_session, factories):
        ticket = factories.AuthTicket(updated=datetime.utcnow())
        db_session.flush()

        expires_before = ticket.expires

        svc.verify_ticket(ticket.user_userid, ticket.id)
        db_session.flush()

        # Manually expire ticket, so that the data will be reloaded from the
        # database.
        db_session.expire(ticket)
        assert expires_before == ticket.expires

    def test_verify_ticket_extends_expiration_when_over_refresh_interval(self, svc, db_session, factories):
        ticket = factories.AuthTicket(updated=(datetime.utcnow() - services.TICKET_REFRESH_INTERVAL))
        db_session.flush()

        expires_before = ticket.expires

        svc.verify_ticket(ticket.user_userid, ticket.id)
        db_session.flush()

        # Manually expire ticket, so that the data will be reloaded from the
        # database.
        db_session.expire(ticket)
        assert expires_before < ticket.expires

    def test_add_ticket_raises_when_user_cannot_be_found(self, svc):
        svc.usersvc.fetch.return_value = None

        with pytest.raises(ValueError) as exc:
            svc.add_ticket('bogus', 'foobar')

        assert str(exc.value) == 'Cannot find user with userid bogus'

    def test_add_ticket_stores_ticket(self, svc, db_session, user, utcnow):
        svc.usersvc.fetch.return_value = user

        utcnow.return_value = datetime(2016, 1, 1, 5, 23, 54)

        svc.add_ticket(user.userid, 'the-ticket-id')

        ticket = db_session.query(models.AuthTicket).first()
        assert ticket.id == 'the-ticket-id'
        assert ticket.user == user
        assert ticket.user_userid == user.userid
        assert ticket.expires == utcnow.return_value + services.TICKET_TTL

    def test_add_ticket_caches_the_userid(self, svc, db_session, user):
        svc.usersvc.fetch.return_value = user

        assert svc._userid is None
        svc.add_ticket(user.userid, 'the-ticket-id')
        assert svc._userid == user.userid

    @pytest.mark.usefixtures('ticket')
    def test_remove_ticket_skips_deleting_when_id_is_None(self, svc, db_session):
        assert db_session.query(models.AuthTicket).count() == 1
        svc.remove_ticket(None)
        assert db_session.query(models.AuthTicket).count() == 1

    @pytest.mark.usefixtures('ticket')
    def test_remove_ticket_skips_deleting_when_id_is_empty(self, svc, db_session):
        assert db_session.query(models.AuthTicket).count() == 1
        svc.remove_ticket('')
        assert db_session.query(models.AuthTicket).count() == 1

    def test_remove_ticket_deletes_ticket(self, svc, ticket, factories, db_session):
        keep = factories.AuthTicket()

        assert db_session.query(models.AuthTicket).count() == 2
        svc.remove_ticket(ticket.id)
        assert db_session.query(models.AuthTicket).get(keep.id) is not None
        assert db_session.query(models.AuthTicket).get(ticket.id) is None

    def test_remove_ticket_clears_userid_cache(self, svc, ticket):
        svc.verify_ticket(ticket.user_userid, ticket.id)

        assert svc._userid is not None
        svc.remove_ticket(ticket.id)
        assert svc._userid is None

    @property
    def principal(self):
        return 'acct:bob@example.org'

    @property
    def ticket_id(self):
        return 'test-ticket-id'

    @pytest.fixture
    def svc(self, db_session, user_service):
        return services.AuthTicketService(db_session, user_service)

    @pytest.fixture
    def principals_for_user(self, patch):
        return patch('h.auth.services.principals_for_user')

    @pytest.fixture
    def ticket(self, factories, user, db_session):
        ticket = factories.AuthTicket(user=user, user_userid=user.userid)
        db_session.flush()
        return ticket

    @pytest.fixture
    def user(self, factories, db_session):
        user = factories.User()
        db_session.add(user)
        db_session.flush()
        return user


@pytest.mark.usefixtures('user_service')
class TestAuthTicketServiceFactory(object):
    def test_it_returns_auth_ticket_service(self, pyramid_request):
        svc = services.auth_ticket_service_factory(None, pyramid_request)
        assert isinstance(svc, services.AuthTicketService)

    def test_it_provides_request_db_as_session(self, pyramid_request):
        svc = services.auth_ticket_service_factory(None, pyramid_request)
        assert svc.session == pyramid_request.db

    def test_it_provides_user_service(self, pyramid_request, user_service):
        svc = services.auth_ticket_service_factory(None, pyramid_request)
        assert svc.usersvc == user_service


class TestOAuthServiceVerifyJWTBearer(object):
    """ Tests for ``OAuthService.verify_jwt_bearer`` """

    def test_it_returns_the_user_and_authclient_from_the_jwt_token(self, svc, claims, authclient, user):
        expected_user = user
        tok = self.jwt_token(claims, authclient.secret)

        result = svc.verify_jwt_bearer(assertion=tok,
                                       grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer')

        assert (expected_user, authclient) == result

    def test_missing_grant_type(self, svc):
        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_jwt_bearer(assertion='jwt-token',
                                  grant_type=None)

        assert exc.value.type == 'unsupported_grant_type'
        assert 'grant type is not supported' in exc.value.message

    def test_unsupported_grant_type(self, svc):
        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_jwt_bearer(assertion='jwt-token',
                                  grant_type='authorization_code')

        assert exc.value.type == 'unsupported_grant_type'
        assert 'grant type is not supported' in exc.value.message

    def test_missing_assertion(self, svc):
        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_jwt_bearer(assertion=None,
                                  grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer')

        assert exc.value.type == 'invalid_request'
        assert 'assertion parameter is missing' in exc.value.message

    def test_non_jwt_assertion(self, svc):
        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_jwt_bearer(assertion='bogus',
                                  grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer')

        assert exc.value.type == 'invalid_grant'
        assert 'invalid JWT signature' in exc.value.message

    def test_missing_jwt_issuer(self, svc, claims, authclient):
        del claims['iss']
        tok = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_jwt_bearer(assertion=tok,
                                  grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer')

        assert exc.value.type == 'invalid_grant'
        assert 'issuer is missing' in exc.value.message

    def test_empty_jwt_issuer(self, svc, claims, authclient):
        claims['iss'] = ''
        tok = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_jwt_bearer(assertion=tok,
                                  grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer')

        assert exc.value.type == 'invalid_grant'
        assert 'issuer is missing' in exc.value.message

    def test_missing_authclient_with_given_jwt_issuer(self, svc, claims, authclient, db_session):
        db_session.delete(authclient)
        db_session.flush()

        tok = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_jwt_bearer(assertion=tok,
                                  grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer')

        assert exc.value.type == 'invalid_grant'
        assert 'issuer is invalid' in exc.value.message

    def test_non_uuid_jwt_issuer(self, svc, claims, authclient, db_session):
        claims['iss'] = 'bogus'
        tok = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_jwt_bearer(assertion=tok,
                                  grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer')

        assert exc.value.type == 'invalid_grant'
        assert 'issuer is invalid' in exc.value.message

    def test_signed_with_different_secret(self, svc, claims):
        tok = self.jwt_token(claims, 'different-secret')

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_jwt_bearer(assertion=tok,
                                  grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer')

        assert exc.value.type == 'invalid_grant'
        assert 'invalid JWT signature' in exc.value.message

    def test_signed_with_unsupported_algorithm(self, svc, claims, authclient):
        tok = self.jwt_token(claims, authclient.secret, algorithm='HS512')

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_jwt_bearer(assertion=tok,
                                  grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer')

        assert exc.value.type == 'invalid_grant'
        assert 'invalid JWT signature algorithm' in exc.value.message

    def test_missing_jwt_audience(self, svc, claims, authclient):
        del claims['aud']
        tok = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_jwt_bearer(assertion=tok,
                                  grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer')

        assert exc.value.type == 'invalid_grant'
        assert 'missing claim aud' in exc.value.message

    def test_invalid_jwt_audience(self, svc, claims, authclient):
        claims['aud'] = 'foobar.org'
        tok = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_jwt_bearer(assertion=tok,
                                  grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer')

        assert exc.value.type == 'invalid_grant'
        assert 'invalid JWT audience' in exc.value.message

    def test_jwt_not_before_in_future(self, svc, claims, authclient):
        claims['nbf'] = self.epoch(delta=timedelta(minutes=5))
        tok = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_jwt_bearer(assertion=tok,
                                  grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer')

        assert exc.value.type == 'invalid_grant'
        assert 'not before is in the future' in exc.value.message

    def test_jwt_expires_with_leeway_in_the_past(self, svc, claims, authclient):
        claims['exp'] = self.epoch(delta=timedelta(minutes=-2))
        tok = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_jwt_bearer(assertion=tok,
                                  grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer')

        assert exc.value.type == 'invalid_grant'
        assert 'token is expired' in exc.value.message

    def test_jwt_issued_at_in_the_future(self, svc, claims, authclient):
        claims['iat'] = self.epoch(delta=timedelta(minutes=2))
        tok = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_jwt_bearer(assertion=tok,
                                  grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer')

        assert exc.value.type == 'invalid_grant'
        assert 'issued at is in the future' in exc.value.message

    def test_missing_jwt_subject(self, svc, claims, authclient):
        del claims['sub']
        tok = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_jwt_bearer(assertion=tok,
                                  grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer')

        assert exc.value.type == 'invalid_grant'
        assert 'subject is missing' in exc.value.message

    def test_empty_jwt_subject(self, svc, claims, authclient):
        claims['sub'] = ''
        tok = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_jwt_bearer(assertion=tok,
                                  grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer')

        assert exc.value.type == 'invalid_grant'
        assert 'subject is missing' in exc.value.message

    def test_user_not_found(self, svc, claims, authclient, user_service):
        user_service.fetch.return_value = None

        tok = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_jwt_bearer(assertion=tok,
                                  grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer')

        assert exc.value.type == 'invalid_grant'
        assert 'user with userid described in subject could not be found' in exc.value.message

    def test_it_raises_when_client_authority_does_not_match_userid(self, svc, db_session, claims, authclient, user):
        user.authority = 'bogus-partner.org'
        db_session.flush()

        claims['sub'] = user.userid
        tok = self.jwt_token(claims, authclient.secret)

        with pytest.raises(OAuthTokenError) as exc:
            svc.verify_jwt_bearer(assertion=tok,
                                  grant_type='urn:ietf:params:oauth:grant-type:jwt-bearer')

        assert exc.value.type == 'invalid_grant'
        assert 'authenticated client and JWT subject authorities do not match' in exc.value

    @pytest.fixture
    def svc(self, pyramid_request, db_session, user_service):
        return services.OAuthService(db_session, user_service, pyramid_request.domain)

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
        user = factories.User(authority=authclient.authority)
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
        return services.OAuthService(db_session, user_service, pyramid_request.domain)

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
        svc = services.oauth_service_factory(None, pyramid_request)
        assert isinstance(svc, services.OAuthService)

    def test_it_provides_request_db_as_session(self, pyramid_request):
        svc = services.oauth_service_factory(None, pyramid_request)
        assert svc.session == pyramid_request.db

    def test_it_provides_user_service(self, pyramid_request, user_service):
        svc = services.oauth_service_factory(None, pyramid_request)
        assert svc.usersvc == user_service

    def test_it_provides_request_domain(self, pyramid_request):
        pyramid_request.domain = 'example.org'
        svc = services.oauth_service_factory(None, pyramid_request)
        assert svc.domain == 'example.org'


@pytest.fixture
def user_service(db_session, pyramid_config):
    service = mock.Mock(spec=UserService(default_authority='example.com',
                                         session=db_session))
    pyramid_config.register_service(service, name='user')
    return service


@pytest.fixture
def utcnow(patch):
    return patch('h.auth.services.utcnow')
