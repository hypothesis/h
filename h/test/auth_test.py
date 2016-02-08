# -*- coding: utf-8 -*-
import pytest

import mock
from pyramid import testing
from pyramid import security

from h import auth


KEY = 'someclient'
SECRET = 'somesecret'


effective_principals_fixtures = pytest.mark.usefixtures('accounts', 'groups')


@effective_principals_fixtures
def test_effective_principals_when_user_is_None(accounts):
    accounts.get_user.return_value = None

    principals = auth.effective_principals('acct:jiji@hypothes.is',
                                           testing.DummyRequest())

    assert principals == [security.Everyone]


@effective_principals_fixtures
def test_effective_principals_returns_Authenticated(accounts, groups):
    # User is authenticated but is not an admin or staff or a member of any
    # groups.
    accounts.get_user.return_value = mock.Mock(admin=False, staff=False)
    groups.group_principals.return_value = []

    principals = auth.effective_principals('acct:jiji@hypothes.is',
                                           testing.DummyRequest())

    assert security.Authenticated in principals


@effective_principals_fixtures
def test_effective_principals_returns_userid(accounts, groups):
    # User is authenticated but is not an admin or staff or a member of any
    # groups.
    accounts.get_user.return_value = mock.Mock(admin=False, staff=False)
    groups.group_principals.return_value = []

    principals = auth.effective_principals('acct:jiji@hypothes.is',
                                           testing.DummyRequest())

    assert 'acct:jiji@hypothes.is' in principals


@effective_principals_fixtures
def test_effective_principals_when_user_is_admin(accounts, groups):
    accounts.get_user.return_value = mock.Mock(admin=True, staff=False)
    groups.group_principals.return_value = []

    principals = auth.effective_principals('acct:jiji@hypothes.is',
                                           testing.DummyRequest())

    assert 'group:__admin__' in principals


@effective_principals_fixtures
def test_effective_principals_when_user_is_staff(accounts, groups):
    accounts.get_user.return_value = mock.Mock(admin=False, staff=True)
    groups.group_principals.return_value = []

    principals = auth.effective_principals('acct:jiji@hypothes.is',
                                           testing.DummyRequest())

    assert 'group:__staff__' in principals


@effective_principals_fixtures
def test_effective_principals_when_user_has_groups(accounts, groups):
    accounts.get_user.return_value = mock.Mock(admin=False, staff=False)
    groups.group_principals.return_value = ['group:abc123', 'group:def456']

    principals = auth.effective_principals('acct:jiji@hypothes.is',
                                           testing.DummyRequest())

    for group in groups.group_principals.return_value:
        assert group in principals


@effective_principals_fixtures
def test_effective_principals_with_staff_admin_and_groups(accounts, groups):
    accounts.get_user.return_value = mock.Mock(admin=True, staff=True)
    groups.group_principals.return_value = ['group:abc123', 'group:def456']

    principals = auth.effective_principals('acct:jiji@hypothes.is',
                                           testing.DummyRequest())

    for principal in [security.Everyone,
                      'group:__admin__',
                      'group:__staff__',
                      'group:abc123',
                      'group:def456',
                      security.Authenticated,
                      'acct:jiji@hypothes.is']:
        assert principal in principals


@pytest.fixture
def accounts(request):
    patcher = mock.patch('h.auth.accounts', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def groups(request):
    patcher = mock.patch('h.auth.groups', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()
