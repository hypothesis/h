# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

import pytest
import mock
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


def test_staff_members_when_no_staff():
    assert models.User.staff_members() == []


def test_staff_members_when_one_staff_member(db_session):
    staff_member = factories.User(staff=True)
    db_session.add(staff_member)

    staff_members = models.User.staff_members()

    assert staff_members == [staff_member]


def test_staff_members_when_multiple_staff_members(db_session):
    staff_members = [factories.User(staff=True) for _ in range(0, 2)]
    db_session.add_all(staff_members)

    result = models.User.staff_members()

    assert result == staff_members


def test_staff_members_does_not_return_non_staff_users(db_session):
    non_staff = [factories.User(staff=False) for _ in range(0, 2)]
    db_session.add_all(non_staff)
    db_session.add_all([factories.User(staff=True) for _ in range(0, 2)])

    staff = models.User.staff_members()

    for non_staff in non_staff:
        assert non_staff not in staff


@mock.patch('h.accounts.models.User.get_by_username')
@mock.patch('h.accounts.models.util.split_user')
def test_get_by_id_with_invalid_id(split_user, get_by_username):
    """If split_user returns None it should return None."""
    split_user.return_value = None

    assert models.User.get_by_id("invalid id") is None
    assert not get_by_username.called


@mock.patch('h.accounts.models.User.get_by_username')
@mock.patch('h.accounts.models.util.split_user')
def test_get_by_id_uses_username_from_split_user(split_user, get_by_username):
    """It should get the username by passing the userid to split_user().

    And it should pass the username to get_by_username().

    """
    split_user.return_value = ("test_username", "test_domain")

    models.User.get_by_id("test_userid")

    split_user.assert_called_once_with("test_userid")
    get_by_username.assert_called_once_with("test_username")


@mock.patch('h.accounts.models.User.get_by_username')
@mock.patch('h.accounts.models.util.split_user')
def test_get_by_id_returns_user(_, get_by_username):
    """It should return when get_by_username() returns.

    If split_user() returns a non-None result then get_by_id() should return
    whatever get_by_username() returns.

    """
    assert models.User.get_by_id("test_userid") == get_by_username.return_value
