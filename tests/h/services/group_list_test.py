from unittest import mock

import pytest
from h_matchers import Any

from h.models.group import Group
from h.services.group_list import GroupListService, group_list_factory
from h.services.group_scope import GroupScopeService


class TestListGroupsSessionGroups:
    def test_it_retrieves_world_group(self, svc, user, default_authority):
        groups = svc.session_groups(default_authority, user)

        assert "__world__" in [group.pubid for group in groups]

    def test_it_excludes_world_group_if_not_found(self, svc, other_authority):
        groups = svc.session_groups(other_authority)

        assert "__world__" not in [group.pubid for group in groups]

    def test_it_includes_user_groups(self, svc, user, default_authority, sample_groups):
        groups = svc.session_groups(default_authority, user)

        assert sample_groups["private"] in groups


class TestAssociatedGroups:
    def test_it_does_not_return_world_group(self, svc, user):
        groups = svc.associated_groups(user)

        assert "__world__" not in [group.pubid for group in groups]

    def test_it_returns_user_private_groups(self, svc, sample_groups, user):
        groups = svc.associated_groups(user)

        assert sample_groups["private"] in groups

    def test_it_returns_restricted_groups_if_user_is_member(self, svc, factories, user):
        restricted_group = factories.RestrictedGroup(
            members=[user], authority=user.authority
        )
        groups = svc.associated_groups(user)

        assert restricted_group in groups

    def test_it_returns_public_groups_if_user_is_creator(
        self, svc, sample_groups, user
    ):
        groups = svc.associated_groups(user)

        # Both the open and restricted groups are in the results even though the
        # user is not a member—the user is the creator, so they are included
        assert sample_groups["open"] in groups
        assert sample_groups["restricted"] in groups

    def test_it_does_not_return_private_groups_if_user_is_not_member(
        self, svc, factories, user
    ):
        # This one's a little interesting. Recall that a user may "leave" a private
        # group. However, that group is not deleted in this case, and they are still
        # the creator of the group. That means that this private group is still associated
        # with this user in some form—but we want to make sure it does not appear
        # in these results.
        private_group = factories.Group(
            creator=user, authority=user.authority, members=[]
        )

        groups = svc.associated_groups(user)

        assert private_group not in groups

    def test_it_returns_empty_list_if_user_is_None(self, svc):
        groups = svc.associated_groups(user=None)

        assert groups == []

    def test_it_does_not_duplicate_groups_in_results(
        self, svc_no_sample_groups, user, factories
    ):
        # This user is both a member of and a creator of this group; make sure it only
        # comes back once
        restricted_group = factories.RestrictedGroup(
            members=[user], authority=user.authority, creator=user
        )

        groups = svc_no_sample_groups.associated_groups(user)

        assert groups == [restricted_group]


class TestListGroupsRequestGroups:
    def test_it_returns_world_group(self, svc, default_authority):
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
        self, svc, default_authority, document_uri, sample_groups
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

        assert not group_scope_service.fetch_by_scope.call_count

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


class TestUserGroups:
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


class TestPrivateGroups:
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


class TestScopedGroups:
    def test_it_fetches_matching_scopes_from_group_scope_service(
        self, svc, default_authority, document_uri, group_scope_service
    ):
        svc.scoped_groups(default_authority, document_uri)

        group_scope_service.fetch_by_scope.assert_called_once_with(document_uri)

    def test_it_returns_empty_list_if_no_matching_scopes(
        self, svc, default_authority, document_uri, group_scope_service
    ):
        group_scope_service.fetch_by_scope.return_value = []

        results = svc.scoped_groups(default_authority, document_uri)

        assert results == []

    def test_it_returns_matching_public_groups(
        self, svc, sample_groups, document_uri, default_authority
    ):
        results = svc.scoped_groups(default_authority, document_uri)

        assert (
            results
            == Any.list.containing(
                [sample_groups["restricted"], sample_groups["open"]]
            ).only()
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


class TestWorldGroup:
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


@pytest.mark.usefixtures("group_scope_service")
class TestGroupListFactory:
    def test_group_list_factory(self, pyramid_request):
        svc = group_list_factory(None, pyramid_request)

        assert isinstance(svc, GroupListService)

    def test_uses_request_default_authority(self, pyramid_request):
        pyramid_request.default_authority = "bar.com"

        svc = group_list_factory(None, pyramid_request)

        assert svc.default_authority == "bar.com"


@pytest.fixture
def other_authority():
    """Return a consistent, different authority for groups in these tests."""
    return "surreptitious.com"


@pytest.fixture
def default_authority(pyramid_request):
    """
    Return the test env request's default authority, i.e. 'example.com'.

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
            name="sample open",
            authority=default_authority,
            scopes=[factories.GroupScope(scope=document_uri)],
            creator=user,
        ),
        "restricted": factories.RestrictedGroup(
            name="sample restricted",
            authority=default_authority,
            scopes=[factories.GroupScope(scope=document_uri)],
            creator=user,
        ),
        "other_authority": factories.OpenGroup(
            name="sample other authority",
            authority=other_authority,
            scopes=[factories.GroupScope(scope=document_uri)],
            creator=user,
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


@pytest.fixture
def svc_no_sample_groups(pyramid_request, pyramid_config, db_session):
    # The way that the group_scope_service is mocked in the main `svc`
    # fixture brings `sample_groups` into the DB. For a clean service with
    # no groups in the DB...here we go
    group_scope_svc = mock.create_autospec(
        GroupScopeService, spec_set=True, instance=True
    )
    pyramid_config.register_service(group_scope_svc, name="group_scope")
    return GroupListService(
        session=db_session,
        default_authority=pyramid_request.default_authority,
        group_scope_service=group_scope_svc,
    )
