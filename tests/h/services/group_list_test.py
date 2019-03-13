# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import mock

from h.services.group_list import GroupListService
from h.services.group_list import group_list_factory
from h.services.group_scope import GroupScopeService
from h.models.group import Group
from h.models.group_scope import GroupScope


class TestListGroupsSessionGroups(object):
    def test_it_retrieves_world_group(self, svc, user, authority):
        svc.world_group = mock.Mock()

        svc.session_groups(authority, user)

        svc.world_group.assert_called_once_with(authority)

    def test_it_includes_world_group_if_world_group_found(self, svc, user, authority):
        svc.world_group = mock.Mock()
        svc.user_groups = mock.Mock()
        svc.user_groups.return_value = (
            []
        )  # No user groups, so world group will be the only group

        groups = svc.session_groups(authority, user)

        assert groups == [svc.world_group.return_value]

    def test_it_excludes_world_group_if_not_found(self, svc, user, authority):
        svc.world_group = mock.Mock()
        svc.world_group.return_value = None  # mocking no world group
        svc.user_groups = mock.Mock()
        svc.user_groups.return_value = []

        groups = svc.session_groups(authority, user)

        assert groups == []

    def test_it_includes_user_groups(self, svc, user, authority):
        svc.user_groups = mock.Mock()
        svc.user_groups.return_value = []

        svc.session_groups(authority, user)

        svc.user_groups.assert_called_once_with(user)

    def test_it_includes_world_and_user_groups(self, svc, user, authority):
        fakeGroup = mock.Mock()
        svc.world_group = mock.Mock()
        svc.user_groups = mock.Mock()
        svc.user_groups.return_value = [fakeGroup]

        groups = svc.session_groups(authority, user)

        assert groups == [svc.world_group.return_value, fakeGroup]


class TestListGroupsRequestGroups(object):
    def test_it_returns_world_group(self, svc, default_authority):
        svc.world_group = mock.Mock()
        svc.request_groups(authority=default_authority)

        svc.world_group.assert_called_once_with(default_authority)

    def test_it_overrides_authority_with_user_authority(self, svc, user, document_uri):
        svc.scoped_groups = mock.Mock()
        svc.scoped_groups.return_value = []
        svc.world_group = mock.Mock()

        svc.request_groups(authority="foople.com", user=user, document_uri=document_uri)

        svc.scoped_groups.assert_called_once_with(user.authority, document_uri)
        svc.world_group.assert_called_once_with(user.authority)

    def test_it_defaults_to_default_authority(
        self, svc, default_authority, document_uri
    ):
        svc.scoped_groups = mock.Mock()
        svc.scoped_groups.return_value = []
        svc.world_group = mock.Mock()

        svc.request_groups(document_uri=document_uri)

        svc.scoped_groups.assert_called_once_with(default_authority, document_uri)
        svc.world_group.assert_called_once_with(default_authority)

    def test_it_returns_results_including_scoped_groups(
        self, svc, authority, document_uri
    ):
        svc.scoped_groups = mock.Mock()
        svc.scoped_groups.return_value = []
        svc.request_groups(authority=authority, document_uri=document_uri)

        svc.scoped_groups.assert_called_once_with(authority, document_uri)

    def test_it_returns_no_scoped_groups_if_uri_missing(self, svc, authority):
        svc.scoped_groups = mock.Mock()
        svc.request_groups(authority=authority)

        svc.scoped_groups.assert_not_called()

    def test_it_returns_private_groups_if_user(self, svc, user, authority):
        svc.private_groups = mock.Mock()
        svc.private_groups.return_value = []

        svc.request_groups(user=user, authority=authority)

        svc.private_groups.assert_called_once_with(user)

    def test_it_returns_no_private_groups_if_no_user(self, svc, authority):
        svc.private_groups = mock.Mock()

        svc.request_groups(authority=authority)

        svc.private_groups.assert_not_called()

    def test_returns_ordered_list_of_groups(self, svc, authority, user, document_uri):
        fake_private_group = mock.Mock()
        fake_scoped_group = mock.Mock()
        fake_world_group = mock.Mock()
        svc.world_group = mock.Mock(return_value=fake_world_group)
        svc.private_groups = mock.Mock(return_value=[fake_private_group])
        svc.scoped_groups = mock.Mock(return_value=[fake_scoped_group])

        results = svc.request_groups(
            authority=authority, user=user, document_uri=document_uri
        )

        assert results == [fake_scoped_group, fake_world_group, fake_private_group]


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
    def test_it_retrieves_all_user_groups(self, svc, user):
        svc.user_groups = mock.Mock(return_value=[])

        svc.private_groups(user)

        svc.user_groups.assert_called_once_with(user)

    def test_it_returns_only_private_groups(self, svc, user, factories):
        private_group = factories.Group()
        open_group = factories.OpenGroup()
        restricted_group = factories.RestrictedGroup()

        user.groups = [private_group, open_group, restricted_group]

        p_groups = svc.private_groups(user)

        assert private_group in p_groups
        assert open_group not in p_groups
        assert restricted_group not in p_groups

    def test_it_returns_empty_list_if_no_user(self, svc):
        p_groups = svc.private_groups(user=None)

        assert p_groups == []


class TestScopedGroups(object):
    def test_it_fetches_matching_scopes_from_group_scope_service(
        self, svc, authority, document_uri, group_scope_service
    ):
        svc.scoped_groups(authority, document_uri)

        group_scope_service.fetch_by_scope.assert_called_once_with(document_uri)

    def test_it_returns_empty_list_if_no_matching_scopes(
        self, svc, authority, document_uri, group_scope_service
    ):
        # TODO this should take a fixture
        group_scope_service.fetch_by_scope.return_value = []

        results = svc.scoped_groups(authority, document_uri)

        assert results == []

    def test_it_only_returns_public_groups(
        self,
        factories,
        svc,
        origin,
        document_uri,
        group_scope_service,
        default_authority,
        db_session,
    ):
        private_group = factories.Group(scopes=[GroupScope(scope=origin)])
        open_group = factories.OpenGroup(scopes=[GroupScope(scope=origin)])
        restricted_group = factories.RestrictedGroup(scopes=[GroupScope(scope=origin)])

        db_session.commit()  # FIXME

        combined_scopes = [
            private_group.scopes[0],
            open_group.scopes[0],
            restricted_group.scopes[0],
        ]

        group_scope_service.fetch_by_scope.return_value = combined_scopes
        results = svc.scoped_groups(default_authority, document_uri)

        assert private_group not in results
        assert open_group in results
        assert restricted_group in results

    def test_it_sorts_groups(
        self,
        factories,
        origin,
        group_scope_service,
        svc,
        default_authority,
        document_uri,
        db_session,
    ):
        groups = [
            factories.OpenGroup(name="Calendar", scopes=[GroupScope(scope=origin)]),
            factories.OpenGroup(name="Braille", scopes=[GroupScope(scope=origin)]),
            factories.OpenGroup(name="Abacus", scopes=[GroupScope(scope=origin)]),
        ]

        db_session.commit()  # FIXME

        group_scope_service.fetch_by_scope.return_value = [
            groups[0].scopes[0],
            groups[1].scopes[0],
            groups[2].scopes[0],
        ]

        results = svc.scoped_groups(default_authority, document_uri)

        assert results[0].name == "Abacus"
        assert results[1].name == "Braille"
        assert results[2].name == "Calendar"

    def test_it_only_returns_groups_matching_authority(
        self,
        factories,
        origin,
        group_scope_service,
        svc,
        default_authority,
        authority,
        document_uri,
        db_session,
    ):
        groups = [
            factories.OpenGroup(
                name="Calendar", scopes=[GroupScope(scope=origin)], authority=authority
            ),
            factories.OpenGroup(name="Braille", scopes=[GroupScope(scope=origin)]),
            factories.OpenGroup(
                name="Abacus", scopes=[GroupScope(scope=origin)], authority=authority
            ),
        ]

        db_session.commit()  # FIXME

        group_scope_service.fetch_by_scope.return_value = [
            groups[0].scopes[0],
            groups[1].scopes[0],
            groups[2].scopes[0],
        ]

        results = svc.scoped_groups(default_authority, document_uri)

        assert len(results) == 1
        assert results[0].name == "Braille"

    def test_it_de_dupes_matching_groups(
        self,
        svc,
        group_scope_service,
        default_authority,
        origin,
        document_uri,
        factories,
        db_session,
    ):
        # Both of this group's scopes will be a match
        open_group = factories.OpenGroup(
            scopes=[GroupScope(scope=origin), GroupScope(scope=origin)]
        )
        db_session.commit()  # FIXME
        group_scope_service.fetch_by_scope.return_value = open_group.scopes

        results = svc.scoped_groups(default_authority, document_uri)

        # But only one instance of the group is returned
        assert results == [open_group]


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
    def test_group_list_factory(self, pyramid_request, group_scope_service):
        svc = group_list_factory(None, pyramid_request)

        assert isinstance(svc, GroupListService)

    def test_uses_request_default_authority(self, pyramid_request, group_scope_service):
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
def group_scope_service(pyramid_config):
    service = mock.create_autospec(GroupScopeService, spec_set=True, instance=True)
    pyramid_config.register_service(service, name="group_scope")
    return service


@pytest.fixture
def svc(pyramid_request, db_session, group_scope_service):
    return GroupListService(
        session=db_session,
        default_authority=pyramid_request.default_authority,
        group_scope_service=group_scope_service,
    )
