# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

import pytest
from sqlalchemy import exc

from h import db
from h.accounts import models
from h.test import factories


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


def test_admins_when_no_admins():
    assert models.User.admins() == []


def test_admins_when_one_admin():
    admin = factories.User(admin=True)
    db.Session.add(admin)

    admins = models.User.admins()

    assert admins == [admin]


def test_admins_when_multiple_admins():
    admins = [factories.User(admin=True) for _ in range(0, 2)]
    db.Session.add_all(admins)

    result = models.User.admins()

    assert result == admins


def test_admins_does_not_return_non_admin_users():
    non_admins = [factories.User(admin=False) for _ in range(0, 2)]
    db.Session.add_all(non_admins)
    db.Session.add_all([factories.User(admin=True) for _ in range(0, 2)])

    admins = models.User.admins()

    for non_admin in non_admins:
        assert non_admin not in admins


def test_staff_members_when_no_staff():
    assert models.User.staff_members() == []


def test_staff_members_when_one_staff_member():
    staff_member = factories.User(staff=True)
    db.Session.add(staff_member)

    staff_members = models.User.staff_members()

    assert staff_members == [staff_member]


def test_staff_members_when_multiple_staff_members():
    staff_members = [factories.User(staff=True) for _ in range(0, 2)]
    db.Session.add_all(staff_members)

    result = models.User.staff_members()

    assert result == staff_members


def test_staff_members_does_not_return_non_staff_users():
    non_staff = [factories.User(staff=False) for _ in range(0, 2)]
    db.Session.add_all(non_staff)
    db.Session.add_all([factories.User(staff=True) for _ in range(0, 2)])

    staff = models.User.staff_members()

    for non_staff in non_staff:
        assert non_staff not in staff
