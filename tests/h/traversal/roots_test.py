from unittest import mock

import pyramid.authorization
import pyramid.security
import pytest
from pyramid.httpexceptions import HTTPBadRequest

import h.auth
from h.auth import role
from h.exceptions import InvalidUserId
from h.models import AuthClient
from h.services.group import GroupService
from h.traversal.contexts import AnnotationContext, UserContext
from h.traversal.roots import (
    AnnotationRoot,
    AuthClientRoot,
    BulkAPIRoot,
    GroupRoot,
    GroupUpsertRoot,
    OrganizationLogoRoot,
    OrganizationRoot,
    ProfileRoot,
    Root,
    UserRoot,
    UserUserIDRoot,
)


class TestRoot:
    @pytest.mark.parametrize(
        "permission",
        [
            "admin_index",
            "admin_groups",
            "admin_mailer",
            "admin_organizations",
            "admin_users",
            pyramid.security.ALL_PERMISSIONS,
        ],
    )
    def test_it_denies_all_permissions_for_unauthed_request(
        self, set_permissions, pyramid_request, permission
    ):
        set_permissions(None, principals=None)

        context = Root(pyramid_request)

        assert not pyramid_request.has_permission(permission, context)

    @pytest.mark.parametrize(
        "permission",
        [
            "admin_index",
            "admin_groups",
            "admin_mailer",
            "admin_organizations",
            "admin_users",
        ],
    )
    def test_it_assigns_admin_permissions_to_requests_with_staff_role(
        self, set_permissions, pyramid_request, permission
    ):
        set_permissions("acct:adminuser@foo", principals=[role.Staff])

        context = Root(pyramid_request)

        assert pyramid_request.has_permission(permission, context)

    def test_it_assigns_all_permissions_to_requests_with_admin_role(
        self, set_permissions, pyramid_request
    ):
        set_permissions("acct:adminuser@foo", principals=[role.Admin])

        context = Root(pyramid_request)

        assert pyramid_request.has_permission(pyramid.security.ALL_PERMISSIONS, context)


@pytest.mark.usefixtures("group_service", "links_service")
class TestAnnotationRoot:
    def test_it_does_not_assign_create_permission_without_authenticated_user(
        self, set_permissions, pyramid_request
    ):
        set_permissions()

        context = AnnotationRoot(pyramid_request)

        assert not pyramid_request.has_permission("create", context)

    def test_it_assigns_create_permission_to_authenticated_request(
        self, set_permissions, pyramid_request
    ):
        set_permissions(
            "acct:adminuser@foo", principals=[pyramid.security.Authenticated]
        )

        context = AnnotationRoot(pyramid_request)

        assert pyramid_request.has_permission("create", context)

    def test_get_item_fetches_annotation(self, pyramid_request, storage):
        factory = AnnotationRoot(pyramid_request)

        factory["123"]
        storage.fetch_annotation.assert_called_once_with(pyramid_request.db, "123")

    def test_get_item_returns_annotation_resource(self, pyramid_request, storage):
        factory = AnnotationRoot(pyramid_request)
        storage.fetch_annotation.return_value = mock.Mock()

        resource = factory["123"]
        assert isinstance(resource, AnnotationContext)

    def test_get_item_resource_has_right_annotation(self, pyramid_request, storage):
        factory = AnnotationRoot(pyramid_request)
        storage.fetch_annotation.return_value = mock.Mock()

        resource = factory["123"]
        assert resource.annotation == storage.fetch_annotation.return_value

    def test_get_item_raises_when_annotation_is_not_found(
        self, storage, pyramid_request
    ):
        factory = AnnotationRoot(pyramid_request)
        storage.fetch_annotation.return_value = None

        with pytest.raises(KeyError):
            factory["123"]

    def test_get_item_has_right_group_service(
        self, pyramid_request, storage, group_service
    ):
        factory = AnnotationRoot(pyramid_request)
        storage.fetch_annotation.return_value = mock.Mock()

        resource = factory["123"]
        assert resource.group_service == group_service

    def test_get_item_has_right_links_service(
        self, pyramid_request, storage, links_service
    ):
        factory = AnnotationRoot(pyramid_request)
        storage.fetch_annotation.return_value = mock.Mock()

        resource = factory["123"]
        assert resource.links_service == links_service

    @pytest.fixture
    def storage(self, patch):
        return patch("h.traversal.roots.storage")

    @pytest.fixture
    def group_service(self, pyramid_config):
        group_service = mock.Mock(spec_set=["find"])
        pyramid_config.register_service(
            group_service, iface="h.interfaces.IGroupService"
        )
        return group_service

    @pytest.fixture
    def links_service(self, pyramid_config):
        service = mock.Mock()
        pyramid_config.register_service(service, name="links")
        return service


class TestAuthClientRoot:
    def test_getitem_returns_the_right_AuthClient(self, db_session, pyramid_request):
        # Add a couple of noise AuthClients to the DB. It should not return these.
        db_session.add(AuthClient(authority="elifesciences.org"))
        db_session.add(AuthClient(authority="localhost"))

        # The AuthClient that we do expect it to return.
        expected_auth_client = AuthClient(authority="hypothes.is")
        db_session.add(expected_auth_client)

        db_session.flush()

        auth_client = AuthClientRoot(pyramid_request)[expected_auth_client.id]

        assert auth_client == expected_auth_client

    def test_getitem_returns_KeyError_if_no_AuthClients_in_DB(self, pyramid_request):
        auth_client_root = AuthClientRoot(pyramid_request)

        with pytest.raises(KeyError):
            auth_client_root["1d5937d6-73be-11e8-9125-871084ad92cf"]

    def test_getitem_returns_KeyError_if_no_matching_AuthClient_in_DB(
        self, db_session, pyramid_request
    ):
        # Add a couple of noise AuthClients to the DB. It should not return these.
        db_session.add(
            AuthClient(
                authority="elifesciences.org", id="c396be08-73bd-11e8-a791-e76551a909f6"
            )
        )
        db_session.add(
            AuthClient(authority="localhost", id="cf482552-73bd-11e8-a791-c37e5c2510d8")
        )

        auth_client_root = AuthClientRoot(pyramid_request)

        with pytest.raises(KeyError):
            auth_client_root["1d5937d6-73be-11e8-9125-871084ad92cf"]

    def test_getitem_returns_KeyError_if_client_id_is_invalid(self, pyramid_request):
        auth_client_root = AuthClientRoot(pyramid_request)

        with pytest.raises(KeyError):
            auth_client_root["this_is_not_a_valid_UUID"]

    @pytest.mark.parametrize("permission", ("foo", "bar", "admin_oauthclients"))
    def test_getitem_grants_admins_all_permissions_on_the_AuthClient(
        self, db_session, permission, pyramid_request
    ):
        auth_client = AuthClient(authority="hypothes.is")
        db_session.add(auth_client)
        db_session.flush()
        auth_policy = pyramid.authorization.ACLAuthorizationPolicy()

        auth_client = AuthClientRoot(pyramid_request)[auth_client.id]

        assert auth_policy.permits(
            context=auth_client, principals=(h.auth.role.Admin,), permission=permission
        )

    @pytest.mark.parametrize("permission", ("foo", "bar", "admin_oauthclients"))
    def test_getitem_doesnt_grant_non_admins_all_permissions_on_the_AuthClient(
        self, db_session, factories, permission, pyramid_request
    ):
        user = factories.User()
        auth_client = AuthClient(authority="hypothes.is")
        db_session.add(auth_client)
        db_session.flush()
        auth_policy = pyramid.authorization.ACLAuthorizationPolicy()

        auth_client = AuthClientRoot(pyramid_request)[auth_client.id]

        assert not auth_policy.permits(
            context=auth_client,
            # Simulate the principals that a real non-admin request would have: lots of
            # principals but not h.auth.role.Admin.
            principals=(
                pyramid.security.Everyone,
                pyramid.security.Authenticated,
                h.auth.role.Staff,
                "group:__world__",
                "authority:example.com",
                user.userid,
            ),
            permission=permission,
        )


class TestBulkAPIRoot:
    @pytest.mark.parametrize(
        "user,principal,permission_expected",
        (
            (None, None, False),
            ("acct:user@hypothes.is", "client_authority:hypothes.is", False),
            ("acct:user@lms.hypothes.is", "client_authority:lms.hypothes.is", True),
        ),
    )
    def test_it_sets_bulk_action_permission_as_expected(
        self, set_permissions, pyramid_request, user, principal, permission_expected
    ):
        set_permissions(user, principals=[principal])

        context = BulkAPIRoot(pyramid_request)

        assert (
            pyramid_request.has_permission("bulk_action", context)
            == permission_expected
        )


@pytest.mark.usefixtures("organizations")
class TestOrganizationRoot:
    def test_it_returns_the_requested_organization(
        self, organizations, organization_factory
    ):
        organization = organizations[1]

        assert organization_factory[organization.pubid] == organization

    def test_it_404s_if_the_organization_doesnt_exist(self, organization_factory):
        with pytest.raises(KeyError):
            organization_factory["does_not_exist"]

    @pytest.fixture
    def organization_factory(self, pyramid_request):
        return OrganizationRoot(pyramid_request)


@pytest.mark.usefixtures("organizations")
class TestOrganizationLogoRoot:
    def test_it_returns_the_requested_organizations_logo(
        self, organizations, organization_logo_factory
    ):
        organization = organizations[1]
        organization.logo = "<svg>blah</svg>"

        assert organization_logo_factory[organization.pubid] == "<svg>blah</svg>"

    def test_it_404s_if_the_organization_doesnt_exist(self, organization_logo_factory):
        with pytest.raises(KeyError):
            organization_logo_factory["does_not_exist"]

    def test_it_404s_if_the_organization_has_no_logo(
        self, organizations, organization_logo_factory
    ):
        with pytest.raises(KeyError):
            assert organization_logo_factory[organizations[0].pubid]

    @pytest.fixture
    def organization_logo_factory(self, pyramid_request):
        return OrganizationLogoRoot(pyramid_request)


class TestProfileRoot:
    def test_it_assigns_update_permission_with_user_role(
        self, set_permissions, pyramid_request
    ):
        set_permissions("acct:adminuser@foo", principals=[role.User])

        context = ProfileRoot(pyramid_request)

        assert pyramid_request.has_permission("update", context)

    def test_it_does_not_assign_update_permission_without_user_role(
        self, set_permissions, pyramid_request
    ):
        set_permissions("acct:adminuser@foo", principals=["whatever"])

        context = ProfileRoot(pyramid_request)

        assert not pyramid_request.has_permission("update", context)


@pytest.mark.usefixtures("groups", "group_service")
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

    @pytest.fixture
    def groups(self, factories):
        # Add some "noise" groups to the DB.
        # These are groups that we _don't_ expect GroupRoot to return in
        # the tests.
        return [factories.Group(), factories.Group(), factories.Group()]

    @pytest.fixture
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
        return patch("h.traversal.roots.GroupRoot")

    @pytest.fixture
    def GroupUpsertContext(self, patch):
        return patch("h.traversal.roots.contexts.GroupUpsertContext")


@pytest.mark.usefixtures("user_service", "client_authority")
class TestUserRoot:
    def test_it_does_not_assign_create_permission_without_auth_client_role(
        self, pyramid_config, pyramid_request
    ):
        policy = pyramid.authorization.ACLAuthorizationPolicy()
        pyramid_config.testing_securitypolicy("acct:adminuser@foo")
        pyramid_config.set_authorization_policy(policy)

        context = UserRoot(pyramid_request)

        assert not pyramid_request.has_permission("create", context)

    def test_it_assigns_create_permission_to_auth_client_role(
        self, set_permissions, pyramid_request
    ):
        set_permissions("acct:adminuser@foo", principals=[role.AuthClient])

        context = UserRoot(pyramid_request)

        assert pyramid_request.has_permission("create", context)

    def test_it_fetches_the_requested_user(
        self, pyramid_request, user_factory, user_service
    ):
        user_factory["bob"]

        user_service.fetch.assert_called_once_with(
            "bob", pyramid_request.default_authority
        )

    def test_it_proxies_to_client_authority(
        self, pyramid_request, user_factory, client_authority, user_service
    ):
        user_factory["bob"]

        client_authority.assert_called_once_with(pyramid_request)
        user_service.fetch.assert_called_once_with(
            "bob", pyramid_request.default_authority
        )

    def test_it_fetches_with_client_authority_if_present(
        self, pyramid_request, user_factory, client_authority, user_service
    ):
        client_authority.return_value = "something.com"
        user_factory["bob"]

        user_service.fetch.assert_called_once_with("bob", client_authority.return_value)

    def test_it_raises_KeyError_if_the_user_does_not_exist(
        self, user_factory, user_service
    ):
        user_service.fetch.return_value = None

        with pytest.raises(KeyError):
            user_factory["does_not_exist"]

    def test_it_returns_users(self, factories, user_factory, user_service):
        user_service.fetch.return_value = user = factories.User.build()

        assert user_factory[user.username] == user

    @pytest.fixture
    def user_factory(self, pyramid_request):
        return UserRoot(pyramid_request)


@pytest.mark.usefixtures("user_service")
class TestUserUserIDRoot:
    def test_it_fetches_the_requested_user(
        self, pyramid_request, user_userid_root, user_service
    ):
        user_userid_root["acct:bob@example.com"]

        user_service.fetch.assert_called_once_with("acct:bob@example.com")

    def test_it_fails_with_bad_request_if_the_userid_is_invalid(
        self, pyramid_request, user_userid_root, user_service
    ):
        user_service.fetch.side_effect = InvalidUserId("dummy id")

        with pytest.raises(HTTPBadRequest):
            user_userid_root["total_nonsense"]

    def test_it_raises_KeyError_if_the_user_does_not_exist(
        self, user_userid_root, user_service
    ):
        user_service.fetch.return_value = None

        with pytest.raises(KeyError):
            user_userid_root["does_not_exist"]

    def test_it_returns_UserContexts(self, factories, user_userid_root, user_service):
        user_service.fetch.return_value = user = factories.User.build()

        resource = user_userid_root[user.username]

        assert isinstance(resource, UserContext)

    @pytest.fixture
    def user_userid_root(self, pyramid_request):
        return UserUserIDRoot(pyramid_request)


@pytest.fixture
def client_authority(patch):
    client_authority = patch("h.traversal.roots.client_authority")
    client_authority.return_value = None
    return client_authority


@pytest.fixture
def organizations(factories):
    # Add a handful of organizations to the DB to make the test realistic.
    return [factories.Organization() for _ in range(3)]


@pytest.fixture
def set_permissions(pyramid_config):
    default = object()

    def request_with_permissions(user_id=None, principals=default):
        if principals is default:
            principals = [pyramid.security.Everyone]

        policy = pyramid.authorization.ACLAuthorizationPolicy()
        pyramid_config.testing_securitypolicy(user_id, groupids=principals)
        pyramid_config.set_authorization_policy(policy)

    return request_with_permissions
