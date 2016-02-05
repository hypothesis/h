# -*- coding: utf-8 -*-
import pytest

from mock import MagicMock, patch, Mock
from pyramid import testing
from pyramid import security

from h import auth


KEY = 'someclient'
SECRET = 'somesecret'


# The fixtures required to mock all of groupfinder()'s dependencies.
groupfinder_fixtures = pytest.mark.usefixtures('accounts', 'groups')


@groupfinder_fixtures
def test_groupfinder_returns_no_principals(accounts):
    """It should return only [] by default.

    If the request has no client and the user is not an admin or staff member
    nor a member of any group, it should return no additional principals.

    """
    accounts.get_user.return_value = MagicMock(admin=False, staff=False)

    assert auth.groupfinder("acct:jiji@hypothes.is", Mock()) == []


@groupfinder_fixtures
def test_groupfinder_with_admin_user(accounts):
    """If the user is an admin it should return "group:__admin__"."""
    accounts.get_user.return_value = MagicMock(admin=True, staff=False)

    assert "group:__admin__" in auth.groupfinder(
        "acct:jiji@hypothes.is", Mock())


@groupfinder_fixtures
def test_groupfinder_with_staff_user(accounts):
    """If the user is staff it should return a "group:__staff__" principal."""
    accounts.get_user.return_value = MagicMock(admin=False, staff=True)

    assert "group:__staff__" in auth.groupfinder(
        "acct:jiji@hypothes.is", Mock())


@groupfinder_fixtures
def test_groupfinder_admin_and_staff(accounts):
    accounts.get_user.return_value = MagicMock(admin=True, staff=True)

    principals = auth.groupfinder("acct:jiji@hypothes.is", Mock())

    assert "group:__admin__" in principals
    assert "group:__staff__" in principals


@groupfinder_fixtures
def test_groupfinder_calls_group_principals(accounts, groups):
    auth.groupfinder("acct:jiji@hypothes.is", Mock())

    groups.group_principals.assert_called_once_with(
        accounts.get_user.return_value)


@groupfinder_fixtures
def test_groupfinder_with_one_group(groups):
    groups.group_principals.return_value = ['group:group-1']

    additional_principals = auth.groupfinder("acct:jiji@hypothes.is", Mock())

    assert 'group:group-1' in additional_principals


@groupfinder_fixtures
def test_groupfinder_with_three_groups(groups):
    groups.group_principals.return_value = [
        'group:group-1',
        'group:group-2',
        'group:group-3'
    ]

    additional_principals = auth.groupfinder("acct:jiji@Hypothes.is", Mock())

    assert 'group:group-1' in additional_principals
    assert 'group:group-2' in additional_principals
    assert 'group:group-3' in additional_principals


def test_effective_principals_includes_everyone():
    """
    Even if the groupfinder returns None, implying that the userid is not
    recognised, `security.Everyone` should be included in the list of effective
    principals.
    """
    groupfinder = lambda userid, request: None
    request = testing.DummyRequest()

    result = auth.effective_principals('acct:elina@example.com',
                                       request,
                                       groupfinder=groupfinder)

    assert result == [security.Everyone]


def test_effective_principals_includes_authenticated_and_userid():
    """
    If the groupfinder returns the empty list, implying that the userid is
    recognised but is a member of no groups, `security.Authenticated` and the
    passed userid should be included in the list of effective principals.
    """
    groupfinder = lambda userid, request: []
    request = testing.DummyRequest()

    result = auth.effective_principals('acct:elina@example.com',
                                       request,
                                       groupfinder=groupfinder)

    assert set(result) == set([security.Everyone,
                               security.Authenticated,
                               'acct:elina@example.com'])


def test_effective_principals_includes_returned_groupfinder_principals():
    """
    If the groupfinder returns groups, these should be included in the list of
    effective principals.
    """
    groupfinder = lambda userid, request: ['group:foo', 'group:bar']
    request = testing.DummyRequest()

    result = auth.effective_principals('acct:elina@example.com',
                                       request,
                                       groupfinder=groupfinder)

    assert set(result) == set([security.Everyone,
                               security.Authenticated,
                               'acct:elina@example.com',
                               'group:foo',
                               'group:bar'])

def test_effective_principals_calls_groupfinder_with_userid_and_request():
    groupfinder = Mock()
    groupfinder.return_value = []
    request = testing.DummyRequest()

    auth.effective_principals('acct:elina@example.com',
                              request,
                              groupfinder=groupfinder)

    groupfinder.assert_called_with('acct:elina@example.com', request)


@pytest.fixture
def accounts(request):
    patcher = patch('h.auth.accounts', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def groups(request):
    patcher = patch('h.auth.groups', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()
