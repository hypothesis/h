# -*- coding: utf-8 -*-

from collections import namedtuple
import pytest

from pyramid import security

from h.auth import role
from h.auth import util


FakeUser = namedtuple('FakeUser', ['admin', 'staff', 'groups'])
FakeGroup = namedtuple('FakeGroup', ['pubid'])


@pytest.mark.parametrize('user,principals', (
    # User isn't found in the database: they're not authenticated at all
    (None, None),
    # User found but not staff, admin, or a member of any groups: no additional principals
    (FakeUser(admin=False, staff=False, groups=[]),
     []),
    # User is admin: role.Admin should be in principals
    (FakeUser(admin=True, staff=False, groups=[]),
     [role.Admin]),
    # User is staff: role.Staff should be in principals
    (FakeUser(admin=False, staff=True, groups=[]),
     [role.Staff]),
    # User is admin and staff
    (FakeUser(admin=True, staff=True, groups=[]),
     [role.Admin, role.Staff]),
    # User is a member of some groups
    (FakeUser(admin=False, staff=False, groups=[FakeGroup('giraffe'), FakeGroup('elephant')]),
     ['group:giraffe', 'group:elephant']),
    # User is admin, staff, and a member of some groups
    (FakeUser(admin=True, staff=True, groups=[FakeGroup('donkeys')]),
     ['group:donkeys', role.Admin, role.Staff]),
))
def test_groupfinder(user, principals, accounts, pyramid_request):
    accounts.get_user.return_value = user

    result = util.groupfinder('acct:jiji@hypothes.is', pyramid_request)

    if principals is None:
        assert result is None
    else:
        assert set(principals) == set(result)


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
