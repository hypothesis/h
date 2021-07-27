from unittest.mock import sentinel

import pytest

from h.auth import role
from h.security.permissions import Permission
from h.traversal.group import GroupContext, GroupRequiredRoot, GroupRoot


class TestGroupContext:
    def test_it_with_a_group(self, factories, ACL):
        group = factories.Group()

        context = GroupContext(group=group)

        assert context.group == group
        assert context.__acl__() == ACL.for_group.return_value
        ACL.for_group.assert_called_once_with(group)

    @pytest.mark.parametrize(
        "principal,has_upsert", ((role.User, True), ("other", False))
    )
    def test_it_without_a_group(
        self, set_permissions, pyramid_request, principal, has_upsert
    ):
        set_permissions("acct:adminuser@foo", principals=[principal])

        context = GroupContext(group=None)

        assert context.group is None
        assert (
            bool(pyramid_request.has_permission(Permission.Group.UPSERT, context))
            == has_upsert
        )

    @pytest.fixture
    def ACL(self, patch):
        return patch("h.traversal.group.ACL")


@pytest.mark.usefixtures("group_service", "GroupContext_")
class TestGroupRoot:
    @pytest.mark.parametrize(
        "principal,has_create", ((role.User, True), ("other", False))
    )
    def test_it_assigns_create_permission_with_user_role(
        self, set_permissions, pyramid_request, principal, has_create
    ):
        set_permissions("acct:adminuser@foo", principals=[principal])

        context = GroupRoot(pyramid_request)

        assert (
            bool(pyramid_request.has_permission(Permission.Group.CREATE, context))
            == has_create
        )

    def test_it_returns_the_context_from_looking_up_the_group(
        self, pyramid_request, group_service, GroupContext_
    ):
        root = GroupRoot(pyramid_request)

        context = root[sentinel.group_id]

        group_service.fetch.assert_called_once_with(sentinel.group_id)
        GroupContext_.assert_called_once_with(group_service.fetch.return_value)

        assert context == GroupContext_.return_value


@pytest.mark.usefixtures("group_service")
class TestGroupRequiredRoot:
    def test_getitem_returns_fetched_groupcontext_if_not_None(
        self, factories, pyramid_request, GroupContext_
    ):
        GroupContext_.return_value.group = factories.Group()

        context = GroupRequiredRoot(pyramid_request)[sentinel.group_id]

        assert context == GroupContext_.return_value

    def test_getitem_raises_KeyError_if_there_is_no_group(
        self, pyramid_request, GroupContext_
    ):
        GroupContext_.return_value.group = None
        with pytest.raises(KeyError):
            GroupRequiredRoot(pyramid_request)["does_not_exist"]


@pytest.fixture
def GroupContext_(patch):
    return patch("h.traversal.group.GroupContext")
