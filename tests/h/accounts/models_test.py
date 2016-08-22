# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

import pytest
from sqlalchemy import exc

from h.accounts import models
from h.security import password_context


def test_activation_has_asciinumeric_code(db_session):
    act = models.Activation()

    db_session.add(act)
    db_session.flush()

    assert re.match(r'[A-Za-z0-9]{12}', act.code)


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
