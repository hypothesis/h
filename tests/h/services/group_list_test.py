# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import mock

from h.services.group_list import GroupListService
from h.services.group_list import group_list_factory
from h.services.group_scope import GroupScopeService
from h.models.group import Group


class TestListGroupsSessionGroups(object):
    def test_it_retrieves_world_group(self, svc, user, default_authority):
        groups = svc.session_groups(default_authority, user)

        assert "__world__" in [group.pubid for group in groups]

    def test_it_excludes_world_group_if_not_found(self, svc, other_authority):
        groups = svc.session_groups(other_authority)

        assert "__world__" not in [group.pubid for group in groups]

    def test_it_includes_user_groups(self, svc, user, default_authority, sample_groups):
        groups = svc.session_groups(default_authority, user)

        assert sample_groups["private"] in groups


class TestListGroupsRequestGroups(object):
    def test_it_returns_world_group(self, svc, default_authority, sample_groups):
        groups = svc.request_groups(authority=default_authority)

        assert "__world__" in [group.pubid for group in groups]

    def test_user_authority_supersedes_default_authority_for_world_group(
        self, svc, other_authority_user, default_authority
    ):
        groups = svc.request_groups(
            authority=default_authority, user=other_authority_user
        )

        # The world group is on the default_authority but the user's authority
        # is different, so the world group is not returned
        assert "__world__" not in [group.pubid for group in groups]

    def test_it_returns_scoped_groups_for_authority_and_document_uri(
        self, svc, group_scope_service, default_authority, document_uri, sample_groups
    ):
        groups = svc.request_groups(
            authority=default_authority, document_uri=document_uri
        )

        assert sample_groups["open"] in groups
        assert sample_groups["restricted"] in groups
        assert sample_groups["other_authority"] not in groups

    def test_it_returns_no_scoped_groups_if_uri_missing(
        self, svc, default_authority, group_scope_service
    ):
        svc.request_groups(authority=default_authority)

        assert group_scope_service.fetch_by_scope.call_count == 0

    def test_it_returns_private_groups_if_user(
        self, svc, user, default_authority, sample_groups
    ):
        groups = svc.request_groups(user=user, authority=default_authority)

        assert sample_groups["private"] in groups

    def test_it_returns_no_private_groups_if_no_user(
        self, svc, default_authority, sample_groups
    ):
        groups = svc.request_groups(authority=default_authority)

        assert sample_groups["private"] not in groups

    def test_returns_ordered_list_of_groups(
        self, svc, default_authority, user, document_uri, sample_groups
    ):
        groups = svc.request_groups(
            authority=default_authority, user=user, document_uri=document_uri
        )

        assert [group.pubid for group in groups] == [
            sample_groups["open"].pubid,
            sample_groups["restricted"].pubid,
            "__world__",
            sample_groups["private"].pubid,
        ]


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

    @pytest.fixture
    def user_groups(self, user, factories):
        return [
            factories.Group(creator=user, name="Gamma"),
            factories.Group(creator=user, name="Oomph"),
            factories.Group(creator=user, name="Beta"),
            factories.Group(creator=user, name="Alpha"),
        ]


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
        self, svc, default_authority, document_uri, group_scope_service
    ):
        svc.scoped_groups(default_authority, document_uri)

        group_scope_service.fetch_by_scope.assert_called_once_with(document_uri)

    def test_it_returns_empty_list_if_no_matching_scopes(
        self, svc, default_authority, document_uri, sample_groups, group_scope_service
    ):
        group_scope_service.fetch_by_scope.return_value = []

        results = svc.scoped_groups(default_authority, document_uri)

        assert results == []

    def test_it_returns_matching_public_groups(
        self, svc, sample_groups, document_uri, default_authority, matchers
    ):
        results = svc.scoped_groups(default_authority, document_uri)

        assert results == matchers.UnorderedList(
            [sample_groups["restricted"], sample_groups["open"]]
        )

    def test_it_returns_matches_from_authority_only(
        self, svc, sample_groups, document_uri, default_authority
    ):
        results = svc.scoped_groups(default_authority, document_uri)

        assert sample_groups["other_authority"] not in results

    def test_it_de_dupes_groups(
        self, svc, sample_groups, document_uri, default_authority
    ):
        results = svc.scoped_groups(default_authority, document_uri)

        # The mocked GroupScope service returns the scope for the "open"
        # group twice, but the group only appears once in the results
        assert sample_groups["open"] in results
        assert len(results) == 2


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

    def test_it_returns_None_if_no_world_group_for_authority(
        self, svc, other_authority
    ):
        # No "__world__" group exists in THIS test module's authority

        w_group = svc.world_group(other_authority)

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
def other_authority():
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
def user(factories):
    return factories.User()


@pytest.fixture
def other_authority_user(factories, other_authority):
    return factories.User(authority=other_authority)


@pytest.fixture
def origin():
    return "http://foo.com"


@pytest.fixture
def document_uri():
    return "http://foo.com/bar/fun.html"


@pytest.fixture
def sample_groups(factories, other_authority, document_uri, default_authority, user):
    return {
        "open": factories.OpenGroup(
            authority=default_authority,
            scopes=[factories.GroupScope(scope=document_uri)],
        ),
        "restricted": factories.RestrictedGroup(
            authority=default_authority,
            scopes=[factories.GroupScope(scope=document_uri)],
        ),
        "other_authority": factories.OpenGroup(
            authority=other_authority, scopes=[factories.GroupScope(scope=document_uri)]
        ),
        "private": factories.Group(creator=user),
    }


@pytest.fixture
def group_scope_service(pyramid_config, sample_groups):
    service = mock.create_autospec(GroupScopeService, spec_set=True, instance=True)
    service.fetch_by_scope.return_value = [
        sample_groups["open"].scopes[0],
        sample_groups["open"].scopes[0],  # This verifies that the groups are de-duped
        sample_groups["restricted"].scopes[0],
        sample_groups["other_authority"].scopes[0],
    ]
    pyramid_config.register_service(service, name="group_scope")
    return service


@pytest.fixture
def svc(pyramid_request, db_session, group_scope_service):
    return GroupListService(
        session=db_session,
        default_authority=pyramid_request.default_authority,
        group_scope_service=group_scope_service,
    )
