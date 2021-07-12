from unittest.mock import sentinel

import pytest
from pyramid.security import Allow

from h.auth import role
from h.traversal.group import GroupContext, GroupRequiredRoot, GroupRoot


class TestGroupContext:
    def test_it_with_a_group(self, factories):
        group = factories.Group()

        context = GroupContext(group=group)

        assert context.group == group
        assert context.__acl__() == group.__acl__()

    def test_it_without_a_group(self, factories):
        context = GroupContext(group=None)

        assert context.group is None
        assert context.__acl__() == [(Allow, role.User, "upsert")]


@pytest.mark.usefixtures("group_service")
class TestGroupRequiredRoot:
    @pytest.mark.parametrize(
        "principal,has_create", ((role.User, True), ("other", False))
    )
    def test_it_assigns_create_permission_with_user_role(
        self, set_permissions, pyramid_request, principal, has_create
    ):
        set_permissions("acct:adminuser@foo", principals=[principal])

        context = GroupRequiredRoot(pyramid_request)

        assert bool(pyramid_request.has_permission("create", context)) == has_create

    def test_getitem_returns_fetched_group_if_not_None(
        self, factories, group_factory, group_service
    ):
        group = factories.Group()
        group_service.fetch.return_value = group

        assert group_factory[group.pubid] == group

    def test_getitem_raises_KeyError_if_fetch_returns_None(
        self, group_factory, group_service
    ):
        group_service.fetch.return_value = None
        with pytest.raises(KeyError):
            group_factory["does_not_exist"]

    @pytest.fixture(autouse=True)
    def group_noise(self, factories):
        # Add some "noise" groups to the DB that we _don't_ expect get back
        factories.Group.create_batch(size=3)

    @pytest.fixture
    def group_factory(self, pyramid_request):
        return GroupRequiredRoot(pyramid_request)


class TestGroupRoot:
    def test_getitem_returns_empty_upsert_context_if_missing_group(
        self, pyramid_request, group_service, GroupContext
    ):
        root = GroupRoot(pyramid_request)
        group_service.fetch.return_value = sentinel.group

        context = root["group_id"]

        group_service.fetch.assert_called_once_with("group_id")
        assert context == GroupContext.return_value
        GroupContext.assert_called_once_with(group=sentinel.group)

    @pytest.fixture(autouse=True)
    def GroupContext(self, patch):
        return patch("h.traversal.group.GroupContext")
