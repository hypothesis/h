from h.auth import role
from h.traversal.profile import ProfileRoot


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
