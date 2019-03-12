# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import mock

from h.services.group_list import GroupListService
from h.services.group_list import group_list_factory
from h.models.group import Group


class TestListGroupsSessionGroups(object):
    def test_it_returns_no_scoped_open_groups_except_world(
        self, svc, user, default_authority, mixed_groups
    ):
        results = svc.session_groups(user=user, authority=default_authority)

        non_world_groups = [group for group in results if group.pubid != "__world__"]

        for group in non_world_groups:
            assert group.type != "open"

    def test_it_returns_no_unscoped_open_groups(
        self, svc, user, authority, unscoped_open_groups
    ):
        results = svc.session_groups(user=user, authority=authority)

        assert results == []

    def test_it_returns_scoped_restricted_groups_if_user_member(
        self, svc, user, scoped_restricted_user_groups, authority
    ):
        user.groups = scoped_restricted_user_groups
        results = svc.session_groups(user=user, authority=authority)

        assert results == user.groups
        for group in results:
            assert group.type == "restricted"

    def test_it_excludes_scoped_restricted_groups_if_user_not_member(
        self, svc, user, scoped_restricted_groups, authority
    ):
        expected = [
            group for group in scoped_restricted_groups if user in group.members
        ]
        results = svc.session_groups(user=user, authority=authority)

        assert results == expected

    def test_it_returns_the_world_group(self, svc, user, default_authority):
        results = svc.session_groups(user=user, authority=default_authority)

        assert results[0].pubid == "__world__"

    def test_it_returns_world_group_only_if_no_user(
        self,
        svc,
        default_authority,
        unscoped_restricted_groups,
        scoped_restricted_groups,
        unscoped_open_groups,
        scoped_open_groups,
    ):
        results = svc.session_groups(user=None, authority=default_authority)

        assert results[0].pubid == "__world__"
        assert len(results) == 1

    def test_it_returns_private_groups_for_user(
        self, user, svc, authority, private_groups
    ):
        user.groups = private_groups
        results = svc.session_groups(user=user, authority=authority)

        for group in user.groups:
            assert group in results
            assert group.type == "private"

    def test_world_group_is_first(self, user, svc, default_authority, private_groups):
        user.groups = private_groups
        results = svc.session_groups(user=user, authority=default_authority)

        world_group = results.pop(0)
        assert world_group.pubid == "__world__"
        for group in results:
            assert group.type == "private"


class TestListGroupsRequestGroups(object):
    def test_it_returns_world_group(self, svc, default_authority):
        results = svc.request_groups(authority=default_authority)

        assert results[0].pubid == "__world__"

    def test_it_overrides_authority_with_user_authority(self, svc, user):
        svc.scoped_groups = mock.Mock()
        svc.scoped_groups.return_value = []
        svc.world_group = mock.Mock()

        svc.request_groups(authority="foople.com", user=user)

        svc.scoped_groups.assert_called_once_with(user.authority, None)
        svc.world_group.assert_called_once_with(user.authority)

    def test_it_defaults_to_default_authority(self, svc, default_authority):
        svc.scoped_groups = mock.Mock()
        svc.scoped_groups.return_value = []
        svc.world_group = mock.Mock()

        svc.request_groups()

        svc.scoped_groups.assert_called_once_with(default_authority, None)
        svc.world_group.assert_called_once_with(default_authority)

    def test_it_returns_matching_scoped_open_groups(
        self, svc, authority, document_uri, scoped_open_groups
    ):
        results = svc.request_groups(authority=authority, document_uri=document_uri)

        group_names = [group.name for group in results]
        assert set(results) == set(scoped_open_groups)
        assert group_names == ["Antigone", "Blender"]

    def test_it_returns_matching_scoped_restricted_groups(
        self, svc, authority, document_uri, scoped_restricted_groups
    ):
        results = svc.request_groups(authority=authority, document_uri=document_uri)

        group_names = [group.name for group in results]
        assert group_names == ["Affluent", "Forensic"]
        assert set(results) == set(scoped_restricted_groups)

    def test_it_returns_no_scoped_groups_if_uri_missing(
        self, svc, authority, scoped_open_groups, scoped_restricted_groups
    ):
        results = svc.request_groups(authority=authority)

        assert results == []

    def test_it_returns_no_unscoped_open_groups(
        self, svc, authority, scoped_open_groups, unscoped_open_groups
    ):
        results = svc.request_groups(authority=authority)

        assert results == []

    def test_it_returns_no_unscoped_restricted_groups(
        self, svc, authority, unscoped_restricted_groups
    ):
        results = svc.request_groups(authority=authority)

        assert results == []

    def test_it_returns_no_unscoped_restricted_user_groups(
        self, svc, authority, user, unscoped_restricted_groups
    ):
        user.groups = unscoped_restricted_groups
        results = svc.request_groups(user=user, authority=authority)

        assert results == []

    def test_it_returns_private_groups_if_user(
        self, svc, user, authority, private_groups
    ):
        user.groups = private_groups
        results = svc.request_groups(user=user, authority=authority)

        assert results == private_groups

    def test_it_returns_no_group_dupes(
        self,
        svc,
        user,
        authority,
        private_groups,
        document_uri,
        scoped_restricted_user_groups,
    ):
        user.groups = private_groups + scoped_restricted_user_groups
        results = svc.request_groups(
            user=user, authority=authority, document_uri=document_uri
        )

        assert results == scoped_restricted_user_groups + private_groups

    def test_returned_open_groups_must_match_authority(
        self, svc, alternate_authority, unscoped_open_groups, scoped_open_groups
    ):
        results = svc.request_groups(authority=alternate_authority)

        assert results == []

    def test_returned_restricted_groups_must_match_authority(
        self, svc, alternate_authority, scoped_restricted_groups
    ):
        results = svc.request_groups(authority=alternate_authority)

        assert results == []

    def test_groups_are_sorted_by_type(
        self, svc, user, mixed_groups, authority, document_uri
    ):
        expected_sorted_types = ["open", "restricted", "open", "private", "private"]
        results = svc.request_groups(
            user=user, authority=authority, document_uri=document_uri
        )

        assert [group.type for group in results] == expected_sorted_types

    def test_groups_are_sorted_alphabetically(
        self, svc, user, mixed_groups, authority, document_uri
    ):
        expected_sorted_pubids = ["wadsworth", "xander", "yaks", "spectacle", "yams"]
        results = svc.request_groups(
            user=user, authority=authority, document_uri=document_uri
        )

        assert [group.pubid for group in results] == expected_sorted_pubids


class TestUserGroups(object):
    def test_it_returns_all_user_groups_sorted_by_group_name(
        self, svc, user, user_groups
    ):
        user.groups = user_groups

        u_groups = svc.user_groups(user)

        group_names = [group.name for group in u_groups]
        assert group_names == ["Alpha", "Beta", "Gamma", "Oomph"]

    def test_it_returns_empty_list_if_no_user(self, svc):
        u_groups = svc.user_groups(user=None)

        assert u_groups == []


class TestPrivateGroups(object):
    def test_it_returns_a_users_private_groups(self, svc, user, user_groups):
        user.groups = user_groups

        p_groups = svc.private_groups(user)

        group_names = [group.name for group in p_groups]
        assert group_names == ["Alpha", "Beta", "Gamma"]

    def test_it_returns_empty_list_if_no_user(self, svc):
        p_groups = svc.private_groups(user=None)

        assert p_groups == []


@pytest.mark.use_fixtures("scoped_groups")
class TestScopedGroups(object):
    def test_it_returns_scoped_groups_that_match_document_uri_and_authority(
        self, svc, document_uri, authority, scoped_groups
    ):
        s_groups = svc.scoped_groups(authority, document_uri)

        group_names = [group.name for group in s_groups]
        assert group_names == ["Affluent", "Antigone", "Blender", "Forensic"]

    def test_it_returns_empty_list_if_no_scope_matches(self, svc, authority):
        s_groups = svc.scoped_groups(authority, "https://www.whatever.org")

        assert s_groups == []

    def test_it_returns_empty_list_if_no_authority_matches(self, svc, document_uri):
        s_groups = svc.scoped_groups("inventive.org", document_uri)

        assert s_groups == []

    def test_it_returns_empty_list_if_uri_scope_parsing_fails(
        self, svc, document_uri, authority, scope_util
    ):
        scope_util.uri_scope.return_value = None

        s_groups = svc.scoped_groups(authority, document_uri)

        assert s_groups == []


class TestWorldGroup(object):
    def test_it_returns_world_group_if_one_exists_for_authority(
        self, svc, default_authority
    ):
        # Unit test global setup includes the addition of a "__world__" group
        # for the test-env's default authority. So that group exists in the
        # test DB, always
        w_group = svc.world_group(default_authority)

        assert isinstance(w_group, Group)
        assert w_group.pubid == "__world__"

    def test_it_returns_None_if_no_world_group_for_authority(self, svc, authority):
        # No "__world__" group exists in THIS test module's authority

        w_group = svc.world_group(authority)

        assert w_group is None


class TestGroupListFactory(object):
    def test_group_list_factory(self, pyramid_request):
        svc = group_list_factory(None, pyramid_request)

        assert isinstance(svc, GroupListService)

    def test_uses_request_default_authority(self, pyramid_request):
        pyramid_request.default_authority = "bar.com"

        svc = group_list_factory(None, pyramid_request)

        assert svc.default_authority == "bar.com"


@pytest.fixture
def authority():
    """Return a consistent, different authority for groups in these tests"""
    return "surreptitious.com"


@pytest.fixture
def default_authority(pyramid_request):
    """
    Return the test env request's default authority, i.e. 'example.com'

    Return the default authority—this automatically has a `__world__` group
    """
    return pyramid_request.default_authority


@pytest.fixture
def alternate_authority():
    return "bar.com"


@pytest.fixture
def default_user(factories, default_authority):
    return factories.User(authority=default_authority)


@pytest.fixture
def user(factories, authority):
    return factories.User(authority=authority)


@pytest.fixture
def user_groups(user, factories):
    return [
        factories.Group(name="Beta"),
        factories.Group(name="Gamma"),
        factories.RestrictedGroup(name="Oomph"),
        factories.Group(name="Alpha"),
    ]


@pytest.fixture
def origin():
    return "http://foo.com"


@pytest.fixture
def document_uri():
    return "http://foo.com/bar/fun.html"


@pytest.fixture
def scoped_open_groups(factories, authority, origin, user):
    return [
        factories.OpenGroup(
            name="Blender",
            authority=authority,
            creator=user,
            scopes=[factories.GroupScope(scope=origin)],
        ),
        factories.OpenGroup(
            name="Antigone",
            authority=authority,
            scopes=[factories.GroupScope(scope=origin)],
        ),
    ]


@pytest.fixture
def scoped_restricted_groups(factories, authority, origin, user):
    return [
        factories.RestrictedGroup(
            name="Forensic",
            authority=authority,
            creator=user,
            scopes=[factories.GroupScope(scope=origin)],
        ),
        factories.RestrictedGroup(
            name="Affluent",
            authority=authority,
            scopes=[factories.GroupScope(scope=origin)],
        ),
    ]


@pytest.fixture
def scoped_groups(scoped_open_groups, scoped_restricted_groups):
    return scoped_open_groups + scoped_restricted_groups


@pytest.fixture
def unscoped_restricted_groups(factories, authority, user):
    return [
        factories.RestrictedGroup(authority=authority, creator=user),
        factories.RestrictedGroup(authority=authority),
    ]


@pytest.fixture
def scoped_restricted_user_groups(factories, authority, user, origin):
    return [
        factories.RestrictedGroup(
            name="Alpha",
            authority=authority,
            creator=user,
            scopes=[factories.GroupScope(scope=origin)],
        ),
        factories.RestrictedGroup(
            name="Beta",
            authority=authority,
            creator=user,
            scopes=[factories.GroupScope(scope=origin)],
        ),
    ]


@pytest.fixture
def unscoped_open_groups(factories, authority, user):
    return [
        factories.OpenGroup(authority=authority, creator=user),
        factories.OpenGroup(authority=authority),
    ]


@pytest.fixture
def alternate_unscoped_open_groups(factories, alternate_authority):
    return [
        factories.OpenGroup(authority=alternate_authority),
        factories.OpenGroup(authority=alternate_authority),
    ]


@pytest.fixture
def private_groups(factories, authority):
    return [factories.Group(authority=authority), factories.Group(authority=authority)]


@pytest.fixture
def mixed_groups(factories, user, authority, origin):
    """Return a list of open groups with different names and scope/not scoped"""
    user.groups = [
        factories.Group(name="Yams", pubid="yams", authority=authority),
        factories.Group(name="Spectacle", pubid="spectacle", authority=authority),
    ]
    return [
        factories.OpenGroup(name="Zebra", pubid="zebra", authority=authority),
        factories.OpenGroup(
            name="Yaks",
            pubid="yaks",
            authority=authority,
            scopes=[factories.GroupScope(scope=origin)],
        ),
        factories.RestrictedGroup(
            name="Xander",
            pubid="xander",
            authority=authority,
            scopes=[factories.GroupScope(scope=origin)],
        ),
        factories.OpenGroup(
            name="wadsworth",
            pubid="wadsworth",
            authority=authority,
            scopes=[factories.GroupScope(scope=origin)],
        ),
    ]


@pytest.fixture
def scope_util(patch):
    return patch("h.services.group_list.scope_util")


@pytest.fixture
def svc(pyramid_request, db_session):
    return GroupListService(
        session=db_session, default_authority=pyramid_request.default_authority
    )
