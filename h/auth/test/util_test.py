# -*- coding: utf-8 -*-
import pytest

import mock
from pyramid import testing
from pyramid import security

from h.auth import role
from h.auth import util


KEY = 'someclient'
SECRET = 'somesecret'


class FakeContext(object):
    deny_all = False


class PrefixAuthorizationPolicy(object):
    """
    A dummy authorization policy that gives anyone any permission that starts
    with one of their effective principals.

    Unless context.deny_all is True. And then we don't.
    """

    def permits(self, context, principals, permission):
        if getattr(context, 'deny_all'):
            return False
        return permission.startswith(tuple(principals))


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


def test_has_permission_uses_authz_policy_to_establish_permission(config, effective_principals):
    ctx = FakeContext()
    config.set_authorization_policy(PrefixAuthorizationPolicy())
    effective_principals.side_effect = lambda userid, _: [userid, 'anyone']
    request = testing.DummyRequest()

    assert util.has_permission(request, ctx, 'foo', 'foo_eat_cake')
    assert util.has_permission(request, ctx, 'foo', 'foo_dance')
    assert util.has_permission(request, ctx, 'foo', 'anyone_monkey_around')
    assert util.has_permission(request, ctx, 'bar', 'bar_wear_shoes')
    assert util.has_permission(request, ctx, 'bar', 'barricade')
    assert not util.has_permission(request, ctx, 'foo', 'barricade')
    assert not util.has_permission(request, ctx, 'bar', 'read_a_book')
    ctx.deny_all = True
    assert not util.has_permission(request, ctx, 'foo', 'foo_eat_cake')
    assert not util.has_permission(request, ctx, 'foo', 'foo_dance')


@pytest.mark.parametrize("p_in,p_out", [
    # The basics
    ([], []),
    (['acct:donna@example.com'], ['acct:donna@example.com']),
    (['group:foo'], ['group:foo']),

    # Remove pyramid principals
    (['system.Everyone'], []),

    # Remap annotatator principal names
    (['group:__world__'], [security.Everyone]),

    # Normalise multiple principals
    (['me', 'myself', 'me', 'group:__world__', 'group:foo', 'system.Admins'],
     ['me', 'myself', security.Everyone, 'group:foo']),
])
def test_translate_annotation_principals(p_in, p_out):
    result = util.translate_annotation_principals(p_in)

    assert set(result) == set(p_out)


@pytest.fixture
def accounts(patch):
    return patch('h.auth.util.accounts')


@pytest.fixture
def effective_principals(patch):
    return patch('h.auth.util.effective_principals')


@pytest.fixture
def group_principals(patch):
    return patch('h.auth.util.group_principals')
