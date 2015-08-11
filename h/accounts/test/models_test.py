# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

import pytest
import mock
from sqlalchemy import exc

from h.accounts import models
from h.test import factories


# The fixtures required to mock all of get_by_id()'s dependencies.
get_by_id_fixtures = pytest.mark.usefixtures('util', 'get_by_username')


@get_by_id_fixtures
def test_get_by_id_calls_split_user(util):
    """It should call split_user() once with the given userid."""
    util.split_user.return_value = ('fred', 'hypothes.is')

    models.User.get_by_id('hypothes.is', 'acct:fred@hypothes.is')

    util.split_user.assert_called_once_with('acct:fred@hypothes.is')


@get_by_id_fixtures
def test_get_by_id_returns_None_for_TypeError(util):
    """If split_user() raises TypeError it should return None."""
    util.split_user.side_effect = TypeError

    user = models.User.get_by_id('hypothes.is', 'acct:fred@hypothes.is')

    assert user is None


@get_by_id_fixtures
def test_get_by_id_returns_None_if_domain_does_not_match(util):
    util.split_user.return_value = ('fred', 'bizarrohypothes.is')

    result = models.User.get_by_id(
        'hypothes.is',  # Request domain doesn't match the userid domain.
        'acct:fred@bizarrohypothes.is')

    assert result is None


@get_by_id_fixtures
def test_get_by_id_calls_get_by_username(util, get_by_username):
    """It should call get_by_username() once with the username."""
    util.split_user.return_value = ('username', 'domain')

    models.User.get_by_id('domain', 'acct:username@domain')

    get_by_username.assert_called_once_with('username')


@get_by_id_fixtures
def test_get_by_id_returns_user(util, get_by_username):
    """It should return the result from get_by_username()."""
    util.split_user.return_value = ('username', 'domain')

    user = models.User.get_by_id('domain', 'acct:username@domain')

    assert user == get_by_username.return_value


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


@pytest.fixture
def util(request):
    patcher = mock.patch('h.accounts.models.util')
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def get_by_username(request):
    patcher = mock.patch('h.accounts.models.User.get_by_username')
    request.addfinalizer(patcher.stop)
    return patcher.start()
