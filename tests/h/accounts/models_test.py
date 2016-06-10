# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

import pytest
from sqlalchemy import exc

from h import db
from h.accounts import models

from ... import factories


def test_activation_has_asciinumeric_code():
    act = models.Activation()

    db.Session.add(act)
    db.Session.flush()

    assert re.match(r'[A-Za-z0-9]{12}', act.code)


def test_cannot_create_dot_variant_of_user():
    fred = models.User(username='fredbloggs',
                       email='fred@example.com',
                       password='123')
    fred2 = models.User(username='fred.bloggs',
                        email='fred@example.org',
                        password='456')

    db.Session.add(fred)
    db.Session.add(fred2)
    with pytest.raises(exc.IntegrityError):
        db.Session.flush()


def test_cannot_create_case_variant_of_user():
    bob = models.User(username='BobJones',
                      email='bob@example.com',
                      password='123')
    bob2 = models.User(username='bobjones',
                       email='bob@example.org',
                       password='456')

    db.Session.add(bob)
    db.Session.add(bob2)
    with pytest.raises(exc.IntegrityError):
        db.Session.flush()


def test_cannot_create_user_with_too_short_username():
    with pytest.raises(ValueError):
        models.User(username='aa')


def test_cannot_create_user_with_too_long_username():
    with pytest.raises(ValueError):
        models.User(username='1234567890123456789012345678901')


def test_cannot_create_user_with_too_long_email():
    with pytest.raises(ValueError):
        models.User(email='bob@b' + 'o'*100 +'b.com')


def test_cannot_create_user_with_too_short_password():
    with pytest.raises(ValueError):
        models.User(password='a')


def test_User_activate_activates_user():
    user = models.User(username='kiki', email='kiki@kiki.com',
                       password='password')
    activation = models.Activation()
    user.activation = activation
    db.Session.add(user)
    db.Session.flush()

    user.activate()
    db.Session.commit()

    assert user.is_activated
