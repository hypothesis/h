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

    def test_fetch_caches_fetched_users(self, db_session, svc, users):
        jacqui, _, _ = users

        svc.fetch('acct:jacqui@foo.com')
        db_session.delete(jacqui)
        db_session.flush()
        user = svc.fetch('acct:jacqui@foo.com')

        assert user is not None
        assert user.username == 'jacqui'

    def test_fetch_all_retrieves_users_by_userid(self, svc):
        result = svc.fetch_all(['acct:jacqui@foo.com', 'acct:steve@example.com'])

        assert len(result) == 2
        assert isinstance(result[0], User)
        assert isinstance(result[1], User)

    def test_fetch_all_caches_fetched_users(self, db_session, svc, users):
        jacqui, _, _ = users

        svc.fetch_all(['acct:jacqui@foo.com'])
        db_session.delete(jacqui)
        db_session.flush()

        result = svc.fetch_all(['acct:jacqui@foo.com'])
        assert len(result) == 1
        assert result[0].username == 'jacqui'

    def test_fetch_for_login_by_username(self, svc, users):
        _, steve, _ = users
        assert svc.fetch_for_login('steve') is steve

    def test_fetch_for_login_by_email(self, svc, users):
        _, steve, _ = users
        assert svc.fetch_for_login('steve@steveo.com') is steve
        assert svc.fetch_for_login('StEvE@steveo.COM') is steve

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

    def test_sets_up_cache_clearing_on_transaction_end(self, patch, db_session):
        decorator = patch('h.services.user.on_transaction_end')

        UserService(default_authority='example.com', session=db_session)

        decorator.assert_called_once_with(db_session)

    def test_clears_cache_on_transaction_end(self, patch, db_session, users):
        funcs = {}

        # We need to capture the inline `clear_cache` function so we can
        # call it manually later
        def on_transaction_end_decorator(session):
            def on_transaction_end(func):
                funcs['clear_cache'] = func
            return on_transaction_end

        decorator = patch('h.services.user.on_transaction_end')
        decorator.side_effect = on_transaction_end_decorator

        jacqui, _, _ = users
        svc = UserService(default_authority='example.com', session=db_session)
        svc.fetch('acct:jacqui@foo.com')
        db_session.delete(jacqui)

        funcs['clear_cache']()

        user = svc.fetch('acct:jacqui@foo.com')
        assert user is None

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
