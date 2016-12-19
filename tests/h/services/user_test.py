# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.services.user import (
    UserNotActivated,
    UserNotKnown,
    UserService,
    user_service_factory,
)
from h.models import User


@pytest.mark.usefixtures('users')
class TestUserService(object):

    def test_fetch_retrieves_user_by_userid(self, svc):
        result = svc.fetch('acct:jacqui@foo.com')

        assert isinstance(result, User)

    def test_fetch_retrieves_user_by_username_and_authority(self, svc):
        result = svc.fetch('jacqui', 'foo.com')

        assert isinstance(result, User)

    def test_fetch_caches_fetched_users(self, db_session, svc, users):
        jacqui, _, _ = users

        svc.fetch('acct:jacqui@foo.com')
        db_session.delete(jacqui)
        db_session.flush()
        user = svc.fetch('acct:jacqui@foo.com')

        assert user is not None
        assert user.username == 'jacqui'

    def test_flushes_cache_on_session_commit(self, db_session, svc, users):
        jacqui, _, _ = users

        svc.fetch('acct:jacqui@foo.com')
        db_session.delete(jacqui)
        db_session.commit()
        user = svc.fetch('acct:jacqui@foo.com')

        assert user is None

    def test_login_by_username(self, svc, users):
        _, steve, _ = users
        assert svc.login('steve', 'stevespassword') is steve

    def test_login_by_email(self, svc, users):
        _, steve, _ = users
        assert svc.login('steve@steveo.com', 'stevespassword') is steve

    def test_login_bad_password(self, svc):
        assert svc.login('steve', 'incorrect') is None
        assert svc.login('steve@steveo.com', 'incorrect') is None

    def test_login_by_username_wrong_authority(self, svc):
        with pytest.raises(UserNotKnown):
            svc.login('jacqui', 'jacquispassword')

    def test_login_by_email_wrong_authority(self, svc):
        with pytest.raises(UserNotKnown):
            svc.login('jacqui@jj.com', 'jacquispassword')

    def test_login_by_username_not_activated(self, svc):
        with pytest.raises(UserNotActivated):
            svc.login('mirthe', 'mirthespassword')

    def test_login_by_email_not_activated(self, svc, users):
        with pytest.raises(UserNotActivated):
            svc.login('mirthe@deboer.com', 'mirthespassword')

    @pytest.fixture
    def svc(self, db_session):
        return UserService(default_authority='example.com', session=db_session)

    @pytest.fixture
    def users(self, db_session, factories):
        users = [factories.User(username='jacqui',
                                email='jacqui@jj.com',
                                authority='foo.com',
                                password='jacquispassword'),
                 factories.User(username='steve',
                                email='steve@steveo.com',
                                authority='example.com',
                                password='stevespassword'),
                 factories.User(username='mirthe',
                                email='mirthe@deboer.com',
                                authority='example.com',
                                password='mirthespassword',
                                inactive=True)]
        db_session.add_all(users)
        db_session.flush()
        return users


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
