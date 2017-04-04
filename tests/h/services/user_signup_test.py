# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from h.models import Activation, Subscriptions, User
from h.services.user_password import UserPasswordService
from h.services.user_signup import (
    UserSignupService,
    user_signup_service_factory,
)


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

    def test_signup_does_not_create_activation_for_user_when_activation_not_required(self, svc):
        user = svc.signup(require_activation=False,
                          username='foo',
                          email='foo@bar.com')

        assert user.activation is None

    def test_signup_sets_default_authority(self, svc):
        user = svc.signup(username='foo', email='foo@bar.com')

        assert user.authority == 'example.org'

    def test_signup_allows_authority_override(self, svc):
        user = svc.signup(username='foo',
                          email='foo@bar.com',
                          authority='bar-client.com')

        assert user.authority == 'bar-client.com'

    def test_signup_sets_password_using_password_service(self, svc, user_password_service):
        user = svc.signup(username='foo',
                          email='foo@bar.com',
                          password='wibble')

        user_password_service.update_password.assert_called_once_with(user, 'wibble')
        assert user.password == 'fakehash'

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

    def test_signup_does_not_send_email_when_activation_not_required(self, mailer, svc):
        svc.signup(require_activation=False,
                   username='foo',
                   email='foo@bar.com')

        assert not mailer.send.delay.called

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
    def svc(self, db_session, mailer, signup_email, user_password_service):
        return UserSignupService(default_authority='example.org',
                                 mailer=mailer,
                                 session=db_session,
                                 password_service=user_password_service,
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


@pytest.mark.usefixtures('user_password_service')
class TestUserSignupServiceFactory(object):
    def test_returns_user_signup_service(self, pyramid_request):
        svc = user_signup_service_factory(None, pyramid_request)

        assert isinstance(svc, UserSignupService)

    def test_provides_request_authority_as_default_authority(self, pyramid_request):
        svc = user_signup_service_factory(None, pyramid_request)

        assert svc.default_authority == pyramid_request.authority

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

    def test_provides_user_password_service(self, pyramid_request):
        svc = user_signup_service_factory(None, pyramid_request)
        password_svc = pyramid_request.find_service(name='user_password')

        assert svc.password_service == password_svc

    def test_provides_request_stats_as_stats(self, pyramid_request):
        svc = user_signup_service_factory(None, pyramid_request)

        assert svc.stats == pyramid_request.stats


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.stats = mock.Mock(spec_set=['incr'])
    return pyramid_request


@pytest.fixture
def user_password_service(pyramid_config):
    service = mock.Mock(spec_set=UserPasswordService())

    def password_setter(user, password):
        user.password = 'fakehash'
    service.update_password.side_effect = password_setter

    pyramid_config.register_service(service, name='user_password')
    return service
