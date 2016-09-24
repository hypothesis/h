# -*- coding: utf-8 -*-

from collections import namedtuple
import pytest
import mock

from pyramid import security

from h.auth import role
from h.auth import util


FakeUser = namedtuple('FakeUser', ['admin', 'staff', 'groups'])
FakeGroup = namedtuple('FakeGroup', ['pubid'])


class TestGroupfinder(object):
    def test_it_fetches_the_user(self, pyramid_request, user_service):
        util.groupfinder('acct:bob@example.org', pyramid_request)
        user_service.fetch.assert_called_once_with('acct:bob@example.org')

    def test_it_returns_principals_for_user(self,
                                            pyramid_request,
                                            user_service,
                                            principals_for_user):
        result = util.groupfinder('acct:bob@example.org', pyramid_request)

        principals_for_user.assert_called_once_with(user_service.fetch.return_value)
        assert result == principals_for_user.return_value


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
def test_principals_for_user(user, principals):
    result = util.principals_for_user(user)

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
def user_service(pyramid_config):
    service = mock.Mock(spec_set=['fetch'])
    service.fetch.return_value = None
    pyramid_config.register_service(service, name='user')
    return service

@pytest.fixture
def principals_for_user(patch):
    return patch('h.auth.util.principals_for_user')
