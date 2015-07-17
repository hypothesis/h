# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

import pytest
from sqlalchemy import exc

from h.accounts import models
from h.test import factories


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


def test_admins_when_no_admins():
    assert models.User.admins() == []


def test_admins_when_one_admin(db_session):
    admin = factories.User(admin=True)
    db_session.add(admin)

    admins = models.User.admins()

    assert admins == [admin]


def test_admins_when_multiple_admins(db_session):
    admins = [factories.User(admin=True) for _ in range(0, 2)]
    db_session.add_all(admins)

    result = models.User.admins()

    assert result == admins


def test_admins_does_not_return_non_admin_users(db_session):
    non_admins = [factories.User(admin=False) for _ in range(0, 2)]
    db_session.add_all(non_admins)
    db_session.add_all([factories.User(admin=True) for _ in range(0, 2)])

    admins = models.User.admins()

    for non_admin in non_admins:
        assert non_admin not in admins
