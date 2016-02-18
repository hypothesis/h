# -*- coding: utf-8 -*-
import pytest

import mock
from pyramid import testing
from pyramid import security

from h.auth import role
from h.auth import util
from h.api.models.token import API_TOKEN_PREFIX


KEY = 'someclient'
SECRET = 'somesecret'


effective_principals_fixtures = pytest.mark.usefixtures('accounts', 'group_principals')


@effective_principals_fixtures
def test_effective_principals_when_user_is_None(accounts):
    accounts.get_user.return_value = None

    principals = util.effective_principals('acct:jiji@hypothes.is',
                                           testing.DummyRequest())

    assert principals == [security.Everyone]


@effective_principals_fixtures
def test_effective_principals_returns_Authenticated(accounts, group_principals):
    # User is authenticated but is not an admin or staff or a member of any
    # groups.
    accounts.get_user.return_value = mock.Mock(admin=False, staff=False)
    group_principals.return_value = []

    principals = util.effective_principals('acct:jiji@hypothes.is',
                                           testing.DummyRequest())

    assert security.Authenticated in principals


@effective_principals_fixtures
def test_effective_principals_returns_userid(accounts, group_principals):
    # User is authenticated but is not an admin or staff or a member of any
    # groups.
    accounts.get_user.return_value = mock.Mock(admin=False, staff=False)
    group_principals.return_value = []

    principals = util.effective_principals('acct:jiji@hypothes.is',
                                           testing.DummyRequest())

    assert 'acct:jiji@hypothes.is' in principals


@effective_principals_fixtures
def test_effective_principals_when_user_is_admin(accounts, group_principals):
    accounts.get_user.return_value = mock.Mock(admin=True, staff=False)
    group_principals.return_value = []

    principals = util.effective_principals('acct:jiji@hypothes.is',
                                           testing.DummyRequest())

    assert role.Admin in principals


@effective_principals_fixtures
def test_effective_principals_when_user_is_staff(accounts, group_principals):
    accounts.get_user.return_value = mock.Mock(admin=False, staff=True)
    group_principals.return_value = []

    principals = util.effective_principals('acct:jiji@hypothes.is',
                                           testing.DummyRequest())

    assert role.Staff in principals


@effective_principals_fixtures
def test_effective_principals_when_user_has_groups(accounts, group_principals):
    accounts.get_user.return_value = mock.Mock(admin=False, staff=False)
    group_principals.return_value = ['group:abc123', 'group:def456']

    principals = util.effective_principals('acct:jiji@hypothes.is',
                                           testing.DummyRequest())

    for group in group_principals.return_value:
        assert group in principals


@effective_principals_fixtures
def test_effective_principals_with_staff_admin_and_groups(accounts, group_principals):
    accounts.get_user.return_value = mock.Mock(admin=True, staff=True)
    group_principals.return_value = ['group:abc123', 'group:def456']

    principals = util.effective_principals('acct:jiji@hypothes.is',
                                           testing.DummyRequest())

    for principal in [security.Everyone,
                      role.Admin,
                      role.Staff,
                      'group:abc123',
                      'group:def456',
                      security.Authenticated,
                      'acct:jiji@hypothes.is']:
        assert principal in principals


def _mock_group(pubid):
    return mock.Mock(pubid=pubid)


def test_group_principals_with_no_groups():
    user = mock.Mock(groups=[])

    assert util.group_principals(user) == []


def test_group_principals_with_one_group():
    user = mock.Mock(groups=[_mock_group('pubid1')])

    assert util.group_principals(user) == ['group:pubid1']


def test_group_principals_with_three_groups():
    user = mock.Mock(groups=[
        _mock_group('pubid1'),
        _mock_group('pubid2'),
        _mock_group('pubid3'),
    ])

    assert util.group_principals(user) == [
        'group:pubid1',
        'group:pubid2',
        'group:pubid3',
    ]


def test_bearer_token_returns_token():
    request = testing.DummyRequest(headers={
        'Authorization': 'Bearer ' + API_TOKEN_PREFIX + 'abc123'
    })

    assert util.bearer_token(request) == API_TOKEN_PREFIX + 'abc123'


def test_bearer_token_when_no_Authorization_header():
    request = testing.DummyRequest(headers={})

    assert util.bearer_token(request) == ''


def test_bearer_token_when_Authorization_header_does_not_contain_bearer():
    request = testing.DummyRequest(headers={
        'Authorization': API_TOKEN_PREFIX + 'abc123'  # No "Bearer " prefix.
    })

    assert util.bearer_token(request) == ''


@pytest.fixture
def accounts(request):
    patcher = mock.patch('h.auth.util.accounts', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def group_principals(request):
    patcher = mock.patch('h.auth.util.group_principals', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()
