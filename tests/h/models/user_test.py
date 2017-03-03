# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import mock
import pytest
from sqlalchemy import exc

from h import models
from h.services.user import user_service_factory
from h.models.user import UserFactory
from h.security import password_context


@pytest.mark.usefixtures('user_service')
class TestUserFactory(object):

    def test_it_raises_KeyError_if_the_user_does_not_exist(self,
                                                           user_factory,
                                                           user_service):
        user_service.fetch.return_value = None

        with pytest.raises(KeyError):
            user_factory["does_not_exist"]

    def test_it_returns_users(self, factories, user_factory, user_service):
        user_service.fetch.return_value = user = factories.User.build()

        assert user_factory[user.username] == user

    @pytest.fixture
    def user_factory(self, pyramid_request):
        return UserFactory(pyramid_request)

    @pytest.fixture
    def user_service(self, pyramid_config, pyramid_request):
        user_service = mock.Mock(spec_set=user_service_factory(
            None, pyramid_request))
        pyramid_config.register_service(user_service, name='user')
        return user_service


def test_cannot_create_dot_variant_of_user(db_session):
    fred = models.User(authority='example.com',
                       username='fredbloggs',
                       email='fred@example.com')
    fred2 = models.User(authority='example.com',
                        username='fred.bloggs',
                        email='fred@example.org')

    db_session.add(fred)
    db_session.add(fred2)
    with pytest.raises(exc.IntegrityError):
        db_session.flush()


def test_cannot_create_case_variant_of_user(db_session):
    bob = models.User(authority='example.com',
                      username='BobJones',
                      email='bob@example.com')
    bob2 = models.User(authority='example.com',
                       username='bobjones',
                       email='bob@example.org')

    db_session.add(bob)
    db_session.add(bob2)
    with pytest.raises(exc.IntegrityError):
        db_session.flush()


def test_filtering_by_username_matches_dot_variant_of_user(db_session):
    fred = models.User(authority='example.com',
                       username='fredbloggs',
                       email='fred@example.com')
    db_session.add(fred)
    db_session.flush()

    result = db_session.query(models.User).filter_by(username='fred.bloggs').one()

    assert result == fred


def test_filtering_by_username_matches_case_variant_of_user(db_session):
    fred = models.User(authority='example.com',
                       username='fredbloggs',
                       email='fred@example.com')
    db_session.add(fred)
    db_session.flush()

    result = db_session.query(models.User).filter_by(username='FredBloggs').one()

    assert result == fred


def test_userid_derived_from_username_and_authority():
    fred = models.User(authority='example.net',
                       username='fredbloggs',
                       email='fred@example.com')

    assert fred.userid == 'acct:fredbloggs@example.net'


def test_userid_as_class_property(db_session):
    fred = models.User(authority='example.net',
                       username='fredbloggs',
                       email='fred@example.com')
    db_session.add(fred)
    db_session.flush()

    result = (db_session.query(models.User)
              .filter_by(userid='acct:fredbloggs@example.net')
              .one())

    assert result == fred


def test_userid_as_class_property_invalid_userid(db_session):
    # This is to ensure that we don't expose the ValueError that could
    # potentially be thrown by split_user.

    result = (db_session.query(models.User)
              .filter_by(userid='fredbloggsexample.net')
              .all())

    assert result == []


def test_cannot_create_user_with_too_short_username():
    with pytest.raises(ValueError):
        models.User(username='aa')


def test_cannot_create_user_with_too_long_username():
    with pytest.raises(ValueError):
        models.User(username='1234567890123456789012345678901')


def test_cannot_create_user_with_invalid_chars():
    with pytest.raises(ValueError):
        models.User(username='foo-bar')


def test_cannot_create_user_with_too_long_email():
    with pytest.raises(ValueError):
        models.User(email='bob@b' + 'o'*100 +'b.com')


def test_cannot_create_user_with_too_short_password():
    with pytest.raises(ValueError):
        models.User(password='a')


def test_check_password_false_with_null_password():
    user = models.User(username='barnet')

    assert not user.check_password('anything')


def test_check_password_false_with_empty_password():
    user = models.User(username='barnet')
    user._password = ''

    assert not user.check_password('')


def test_check_password_true_with_matching_password():
    user = models.User(username='barnet', password='s3cr37')

    assert user.check_password('s3cr37')


def test_check_password_false_with_incorrect_password():
    user = models.User(username='barnet', password='s3cr37')

    assert not user.check_password('somethingelse')


def test_check_password_validates_old_style_passwords():
    user = models.User(username='barnet')
    user.salt = 'somesalt'
    # Generated with passlib.hash.bcrypt.encrypt('foobar' + 'somesalt', rounds=10)
    user._password = '$2a$10$il7Mi/T5WtvbqP5m3dbjeeohDf5XeDx35N5tdwyJ8uRB35NnIlozy'

    assert user.check_password('foobar')
    assert not user.check_password('somethingelse')


def test_check_password_upgrades_old_style_passwords():
    user = models.User(username='barnet')
    user.salt = 'somesalt'
    # Generated with passlib.hash.bcrypt.encrypt('foobar' + 'somesalt', rounds=10)
    user._password = '$2a$10$il7Mi/T5WtvbqP5m3dbjeeohDf5XeDx35N5tdwyJ8uRB35NnIlozy'

    user.check_password('foobar')

    assert user.salt is None
    assert not password_context.needs_update(user._password)


def test_check_password_only_upgrades_when_password_is_correct():
    user = models.User(username='barnet')
    user.salt = 'somesalt'
    # Generated with passlib.hash.bcrypt.encrypt('foobar' + 'somesalt', rounds=10)
    user._password = '$2a$10$il7Mi/T5WtvbqP5m3dbjeeohDf5XeDx35N5tdwyJ8uRB35NnIlozy'

    user.check_password('donkeys')

    assert user.salt is not None
    assert password_context.needs_update(user._password)


def test_check_password_works_after_upgrade():
    user = models.User(username='barnet')
    user.salt = 'somesalt'
    # Generated with passlib.hash.bcrypt.encrypt('foobar' + 'somesalt', rounds=10)
    user._password = '$2a$10$il7Mi/T5WtvbqP5m3dbjeeohDf5XeDx35N5tdwyJ8uRB35NnIlozy'

    user.check_password('foobar')

    assert user.check_password('foobar')


def test_check_password_upgrades_new_style_passwords():
    user = models.User(username='barnet')
    # Generated with passlib.hash.bcrypt.encrypt('foobar', rounds=4, ident='2b')
    user._password = '$2b$04$L2j.vXxlLt9JJNHHsy0EguslcaphW7vssSpHbhqCmf9ECsMiuTd1y'

    user.check_password('foobar')

    assert not password_context.needs_update(user._password)


def test_setting_password_unsets_salt():
    user = models.User(username='barnet')
    user.salt = 'somesalt'
    user._password = 'whatever'

    user.password = 'flibble'

    assert user.salt is None
    assert user.check_password('flibble')


def test_User_activate_activates_user(db_session):
    user = models.User(authority='example.com',
                       username='kiki',
                       email='kiki@kiki.com')
    activation = models.Activation()
    user.activation = activation
    db_session.add(user)
    db_session.flush()

    user.activate()
    db_session.commit()

    assert user.is_activated


class TestUserGetByEmail(object):
    def test_it_returns_a_user(self, db_session, users):
        user = users['meredith']
        actual = models.User.get_by_email(db_session, user.email, user.authority)
        assert actual == user

    def test_it_filters_by_email(self, db_session, users):
        authority = 'example.com'
        email = 'bogus@msn.com'

        actual = models.User.get_by_email(db_session, email, authority)
        assert actual is None

    def test_it_filters_email_case_insensitive(self, db_session, users):
        user = users['emily']
        mixed_email = 'eMiLy@mSn.com'

        actual = models.User.get_by_email(db_session, mixed_email, user.authority)
        assert actual == user

    def test_it_filters_by_authority(self, db_session, users):
        user = users['norma']

        actual = models.User.get_by_email(db_session, user.email, 'example.com')
        assert actual is None

    @pytest.fixture
    def users(self, db_session, factories):
        users = {
            'emily': factories.User(username='emily', email='emily@msn.com', authority='example.com'),
            'norma': factories.User(username='norma', email='norma@foo.org', authority='foo.org'),
            'meredith': factories.User(username='meredith', email='meredith@gmail.com', authority='example.com'),
        }
        db_session.flush()
        return users


class TestUserGetByUsername(object):
    def test_it_returns_a_user(self, db_session, users):
        user = users['meredith']

        actual = models.User.get_by_username(db_session, user.username, user.authority)
        assert actual == user

    def test_it_filters_by_username(self, db_session):
        authority = 'example.com'
        username = 'bogus'

        actual = models.User.get_by_username(db_session, username, authority)
        assert actual is None

    def test_it_filters_by_authority(self, db_session, users):
        user = users['norma']

        actual = models.User.get_by_username(db_session, user.username, 'example.com')
        assert actual is None

    @pytest.fixture
    def users(self, db_session, factories):
        users = {
            'emily': factories.User(username='emily', authority='example.com'),
            'norma': factories.User(username='norma', authority='foo.org'),
            'meredith': factories.User(username='meredith', authority='example.com'),
        }
        db_session.flush()
        return users
