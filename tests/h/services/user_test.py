# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.models import User
from h.services.user import UserNotActivated, UserService, user_service_factory


@pytest.mark.usefixtures('users')
class TestUserService(object):
    def test_fetch_retrieves_user_by_userid(self, svc):
        result = svc.fetch('acct:jacqui@foo.com')

        assert isinstance(result, User)

    def test_fetch_retrieves_user_by_username_and_authority(self, svc):
        result = svc.fetch('jacqui', 'foo.com')

        assert isinstance(result, User)

    def test_fetch_for_login_by_username(self, svc, users):
        _, steve, _ = users
        assert svc.fetch_for_login('steve') is steve

    def test_fetch_for_login_by_email(self, svc, users):
        _, steve, _ = users
        assert svc.fetch_for_login('steve@steveo.com') is steve

    def test_fetch_for_login_by_username_wrong_authority(self, svc):
        assert svc.fetch_for_login('jacqui') is None

    def test_fetch_for_login_by_email_wrong_authority(self, svc):
        assert svc.fetch_for_login('jacqui@jj.com') is None

    def test_fetch_for_login_by_username_not_activated(self, svc):
        with pytest.raises(UserNotActivated):
            svc.fetch_for_login('mirthe')

    def test_fetch_for_login_by_email_not_activated(self, svc, users):
        with pytest.raises(UserNotActivated):
            svc.fetch_for_login('mirthe@deboer.com')

    def test_update_preferences_tutorial_enable(self, svc, factories):
        user = factories.User.build(sidebar_tutorial_dismissed=True)

        svc.update_preferences(user, show_sidebar_tutorial=True)

        assert user.sidebar_tutorial_dismissed is False

    def test_update_preferences_tutorial_disable(self, svc, factories):
        user = factories.User.build(sidebar_tutorial_dismissed=False)

        svc.update_preferences(user, show_sidebar_tutorial=False)

        assert user.sidebar_tutorial_dismissed is True

    def test_update_preferences_raises_for_unsupported_keys(self, svc, factories):
        user = factories.User.build()

        with pytest.raises(TypeError) as exc:
            svc.update_preferences(user, foo='bar', baz='qux')

        assert 'keys baz, foo are not allowed' in exc.value.message

    @pytest.fixture
    def svc(self, db_session):
        return UserService(default_authority='example.com', session=db_session)

    @pytest.fixture
    def users(self, db_session, factories):
        users = [factories.User(username='jacqui',
                                email='jacqui@jj.com',
                                authority='foo.com'),
                 factories.User(username='steve',
                                email='steve@steveo.com',
                                authority='example.com'),
                 factories.User(username='mirthe',
                                email='mirthe@deboer.com',
                                authority='example.com',
                                inactive=True)]
        db_session.flush()
        return users


class TestUserServiceFactory(object):
    def test_returns_user_service(self, pyramid_request):
        svc = user_service_factory(None, pyramid_request)

        assert isinstance(svc, UserService)

    def test_provides_request_authority_as_default_authority(self, pyramid_request):
        svc = user_service_factory(None, pyramid_request)

        assert svc.default_authority == pyramid_request.authority

    def test_provides_request_db_as_session(self, pyramid_request):
        svc = user_service_factory(None, pyramid_request)

        assert svc.session == pyramid_request.db
