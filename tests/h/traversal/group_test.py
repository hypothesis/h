from unittest import mock

import pytest
from pyramid import security
from pyramid.authorization import ACLAuthorizationPolicy

from h.auth import role
from h.services.group import GroupService
from h.traversal.group import GroupRoot, GroupUpsertContext, GroupUpsertRoot


@pytest.mark.usefixtures("group_links_service")
class TestGroupUpsertContext:
    def test_acl_applies_root_upsert_to_user_role_when_no_group(
        self, pyramid_config, pyramid_request
    ):
        policy = ACLAuthorizationPolicy()
        pyramid_config.testing_securitypolicy(
            "acct:adminuser@foo", groupids=[security.Authenticated, role.User]
        )
        pyramid_config.set_authorization_policy(policy)

        context = GroupUpsertContext(group=None, request=pyramid_request)

        assert pyramid_request.has_permission("upsert", context)

    def test_acl_denies_root_upsert_if_no_user_role_and_no_group(
        self, pyramid_config, pyramid_request
    ):
        policy = ACLAuthorizationPolicy()
        pyramid_config.testing_securitypolicy(
            "acct:adminuser@foo", groupids=[security.Authenticated]
        )
        pyramid_config.set_authorization_policy(policy)

        context = GroupUpsertContext(group=None, request=pyramid_request)

        assert not pyramid_request.has_permission("upsert", context)

    def test_acl_applies_group_model_acl_if_group_is_not_None(
        self, pyramid_config, pyramid_request, factories
    ):
        group = factories.Group()
        policy = ACLAuthorizationPolicy()
        pyramid_config.testing_securitypolicy(
            "acct:adminuser@foo", groupids=[security.Authenticated]
        )
        pyramid_config.set_authorization_policy(policy)

        context = GroupUpsertContext(group=group, request=pyramid_request)

        assert context.__acl__() == group.__acl__()

    def test_acl_does_not_apply_root_upsert_permission_if_group_is_not_None(
        self, pyramid_config, pyramid_request, factories
    ):
        group = factories.Group()
        policy = ACLAuthorizationPolicy()
        pyramid_config.testing_securitypolicy(
            "acct:adminuser@foo", groupids=[security.Authenticated, role.User]
        )
        pyramid_config.set_authorization_policy(policy)

        context = GroupUpsertContext(group=group, request=pyramid_request)

        # an `upsert` permission could be present in the ACL via the model IF the current
        # user were the creator, but they're not
        assert not pyramid_request.has_permission("upsert", context)


class TestGroupRoot:
    def test_it_assigns_create_permission_with_user_role(
        self, set_permissions, pyramid_request
    ):
        set_permissions("acct:adminuser@foo", principals=[role.User])

        context = GroupRoot(pyramid_request)

        assert pyramid_request.has_permission("create", context)

    def test_it_does_not_assign_create_permission_without_user_role(
        self, set_permissions, pyramid_request
    ):
        set_permissions("acct:adminuser@foo", principals=["whatever"])

        context = GroupRoot(pyramid_request)

        assert not pyramid_request.has_permission("create", context)

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
    def groups(self, factories):
        # Add some "noise" groups to the DB.
        # These are groups that we _don't_ expect GroupRoot to return in
        # the tests.
        return [factories.Group(), factories.Group(), factories.Group()]

    @pytest.fixture(autouse=True)
    def group_service(self, pyramid_config):
        group_service = mock.create_autospec(GroupService, spec_set=True, instance=True)
        pyramid_config.register_service(group_service, name="group")
        return group_service

    @pytest.fixture
    def group_factory(self, pyramid_request):
        return GroupRoot(pyramid_request)


@pytest.mark.usefixtures("GroupRoot", "GroupUpsertContext")
class TestGroupUpsertRoot:
    def test_getitem_returns_empty_upsert_context_if_missing_group(
        self, pyramid_request, GroupRoot, GroupUpsertContext
    ):
        root = GroupUpsertRoot(pyramid_request)
        GroupRoot.return_value.__getitem__.side_effect = KeyError("bang")

        context = root["whatever"]

        GroupRoot.return_value.__getitem__.assert_called_once_with("whatever")
        assert context == GroupUpsertContext.return_value
        GroupUpsertContext.assert_called_once_with(group=None, request=pyramid_request)

    def test_getitem_returns_populated_upsert_context_if_group_found(
        self, pyramid_request, GroupRoot, GroupUpsertContext, factories
    ):
        group = factories.Group()
        root = GroupUpsertRoot(pyramid_request)
        GroupRoot.return_value.__getitem__.return_value = group

        context = root["agroup"]

        GroupRoot.return_value.__getitem__.assert_called_once_with("agroup")
        assert context == GroupUpsertContext.return_value
        GroupUpsertContext.assert_called_once_with(group=group, request=pyramid_request)

    @pytest.fixture
    def GroupRoot(self, patch):
        return patch("h.traversal.group.GroupRoot")

    @pytest.fixture
    def GroupUpsertContext(self, patch):
        return patch("h.traversal.group.GroupUpsertContext")
