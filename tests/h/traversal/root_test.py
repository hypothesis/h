import pyramid.authorization
import pyramid.security
import pytest

from h.auth import role
from h.security.permissions import Permission
from h.traversal.root import Root


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
            Permission.AdminPage.INDEX,
            Permission.AdminPage.GROUPS,
            Permission.AdminPage.MAILER,
            Permission.AdminPage.ORGANIZATIONS,
            Permission.AdminPage.USERS,
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
