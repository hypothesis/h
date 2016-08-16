# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

import pytest
from sqlalchemy import exc

from h.accounts import models


def test_activation_has_asciinumeric_code(db_session):
    act = models.Activation()

    db_session.add(act)
    db_session.flush()

    assert re.match(r'[A-Za-z0-9]{12}', act.code)


def test_cannot_create_dot_variant_of_user(db_session):
    fred = models.User(username='fredbloggs',
                       email='fred@example.com',
                       password='123')
    fred2 = models.User(username='fred.bloggs',
                        email='fred@example.org',
                        password='456')

    db_session.add(fred)
    db_session.add(fred2)
    with pytest.raises(exc.IntegrityError):
        db_session.flush()


def test_cannot_create_case_variant_of_user(db_session):
    bob = models.User(username='BobJones',
                      email='bob@example.com',
                      password='123')
    bob2 = models.User(username='bobjones',
                       email='bob@example.org',
                       password='456')

    db_session.add(bob)
    db_session.add(bob2)
    with pytest.raises(exc.IntegrityError):
        db_session.flush()


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

def test_User_activate_activates_user(db_session):
    user = models.User(username='kiki', email='kiki@kiki.com',
                       password='password')
    activation = models.Activation()
    user.activation = activation
    db_session.add(user)
    db_session.flush()

    user.activate()
    db_session.commit()

    assert user.is_activated
