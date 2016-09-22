# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from h.accounts.services import (
    UserService,
    UserSignupService,
    user_service_factory,
    user_signup_service_factory,
)
from h.models import Activation, Subscriptions, User


@pytest.mark.usefixtures('users')
class TestUserService(object):

    def test_fetch_retrieves_user_by_userid(self, svc):
        result = svc.fetch('acct:jacqui@foo.com')

        assert isinstance(result, User)

    def test_fetch_caches_fetched_users(self, db_session, svc, users):
        jacqui, _ = users

        svc.fetch('acct:jacqui@foo.com')
        db_session.delete(jacqui)
        db_session.flush()
        user = svc.fetch('acct:jacqui@foo.com')

        assert user is not None
        assert user.username == 'jacqui'

    def test_flushes_cache_on_session_commit(self, db_session, svc, users):
        jacqui, _ = users

        svc.fetch('acct:jacqui@foo.com')
        db_session.delete(jacqui)
        db_session.commit()
        user = svc.fetch('acct:jacqui@foo.com')

        assert user is None

    @pytest.fixture
    def svc(self, db_session):
        return UserService(default_authority='example.com', session=db_session)

    @pytest.fixture
    def users(self, db_session, factories):
        users = [factories.User(username='jacqui', authority='foo.com'),
                 factories.User(username='steve', authority='example.com')]
        db_session.add_all(users)
        db_session.flush()
        return users


class TestUserSignupService(object):
    def test_signup_returns_user(self, svc):
        user = svc.signup(username='foo', email='foo@bar.com')

        assert isinstance(user, User)

    def test_signup_creates_user_in_db(self, db_session, svc):
        svc.signup(username='foo', email='foo@bar.com')

        db_session.commit()
        db_session.close()

        user = db_session.query(User).filter_by(username='foo').one_or_none()

        assert user is not None

    def test_signup_creates_activation_for_user(self, svc):
        user = svc.signup(username='foo', email='foo@bar.com')

        assert isinstance(user.activation, Activation)

    def test_signup_sets_default_authority(self, svc):
        user = svc.signup(username='foo', email='foo@bar.com')

        assert user.authority == 'example.org'

    def test_signup_allows_authority_override(self, svc):
        user = svc.signup(username='foo',
                          email='foo@bar.com',
                          authority='bar-client.com')

        assert user.authority == 'bar-client.com'

    def test_passes_user_info_to_signup_email(self, svc, signup_email):
        user = svc.signup(username='foo', email='foo@bar.com')

        signup_email.assert_called_once_with(id=user.id,
                                             email='foo@bar.com',
                                             activation_code=user.activation.code)

    def test_signup_sends_email(self, mailer, svc):
        svc.signup(username='foo', email='foo@bar.com')

        mailer.send.delay.assert_called_once_with(['test@example.com'],
                                                  'My subject',
                                                  'Text',
                                                  '<p>HTML</p>')

    def test_signup_creates_reply_notification_subscription(self, db_session, svc):
        svc.signup(username='foo', email='foo@bar.com')

        sub = (db_session.query(Subscriptions)
               .filter_by(uri='acct:foo@example.org')
               .one_or_none())

        assert sub.active

    def test_signup_records_stats_if_present(self, svc, stats):
        svc.stats = stats

        svc.signup(username='foo', email='foo@bar.com')

        stats.incr.assert_called_once_with('auth.local.register')

    @pytest.fixture
    def svc(self, db_session, mailer, signup_email):
        return UserSignupService(default_authority='example.org',
                                 mailer=mailer,
                                 session=db_session,
                                 signup_email=signup_email)

    @pytest.fixture
    def mailer(self):
        return mock.Mock(spec_set=['send'])

    @pytest.fixture
    def signup_email(self):
        signup_email = mock.Mock(spec_set=[])
        signup_email.return_value = (['test@example.com'], 'My subject', 'Text', '<p>HTML</p>')
        return signup_email

    @pytest.fixture
    def stats(self):
        return mock.Mock(spec_set=['incr'])


class TestUserServiceFactory(object):
    def test_returns_user_service(self, pyramid_request):
        svc = user_service_factory(None, pyramid_request)

        assert isinstance(svc, UserService)

    def test_provides_request_auth_domain_as_default_authority(self, pyramid_request):
        svc = user_service_factory(None, pyramid_request)

        assert svc.default_authority == pyramid_request.auth_domain

    def test_provides_request_db_as_session(self, pyramid_request):
        svc = user_service_factory(None, pyramid_request)

        assert svc.session == pyramid_request.db


class TestUserSignupServiceFactory(object):
    def test_returns_user_signup_service(self, pyramid_request):
        svc = user_signup_service_factory(None, pyramid_request)

        assert isinstance(svc, UserSignupService)

    def test_provides_request_auth_domain_as_default_authority(self, pyramid_request):
        svc = user_signup_service_factory(None, pyramid_request)

        assert svc.default_authority == pyramid_request.auth_domain

    def test_provides_request_db_as_session(self, pyramid_request):
        svc = user_signup_service_factory(None, pyramid_request)

        assert svc.session == pyramid_request.db

    def test_wraps_email_module_as_signup_email(self, patch, pyramid_request):
        signup_email = patch('h.emails.signup.generate')
        svc = user_signup_service_factory(None, pyramid_request)

        svc.signup_email(id=123, email='foo@bar.com', activation_code='abc456')

        signup_email.assert_called_once_with(pyramid_request,
                                             id=123,
                                             email='foo@bar.com',
                                             activation_code='abc456')

    def test_provides_request_stats_as_stats(self, pyramid_request):
        svc = user_signup_service_factory(None, pyramid_request)

        assert svc.stats == pyramid_request.stats


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.stats = mock.Mock(spec_set=['incr'])
    return pyramid_request
