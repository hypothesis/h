import pytest
from pyramid import security
from pyramid.authorization import ACLAuthorizationPolicy

from h.auth import role
from h.models.group import JoinableBy, ReadableBy, WriteableBy
from h.security.acl import ACL
from h.security.permissions import Permission


class TestACLForGroup:
    def test_authority_joinable(self, group, permits):
        group.joinable_by = JoinableBy.authority

        assert permits(["noise", f"authority:{group.authority}"], Permission.Group.JOIN)
        assert not permits(
            ["noise", f"authority:DIFFERENT_AUTHORITY"], Permission.Group.JOIN
        )

    def test_not_joinable(self, group, permits):
        group.joinable_by = None

        assert not permits(
            ["noise", f"authority:{group.authority}"], Permission.Group.JOIN
        )

    def test_authority_writeable(self, group, permits):
        group.writeable_by = WriteableBy.authority

        assert permits([f"authority:{group.authority}"], Permission.Group.WRITE)

    def test_members_writeable(self, group, permits):
        group.writeable_by = WriteableBy.members

        assert permits([f"group:{group.pubid}"], Permission.Group.WRITE)

    def test_not_writeable(self, group, permitted_principals_for):
        group.writeable_by = None

        assert not permitted_principals_for(Permission.Group.WRITE)

    def test_creator_has_moderate_permission(self, group, permits):
        assert permits(group.creator.userid, Permission.Group.MODERATE)

    def test_no_moderate_permission_when_no_creator(
        self, group, permitted_principals_for
    ):
        group.creator = None

        assert not permitted_principals_for(Permission.Group.MODERATE)

    def test_world_readable_does_not_grant_moderate_permissions(self, group, permits):
        group.readable_by = ReadableBy.world

        assert not permits([security.Authenticated], Permission.Group.MODERATE)
        assert not permits([security.Everyone], Permission.Group.MODERATE)

    def test_non_creator_members_do_not_have_moderate_permission(self, group, permits):
        group.readable_by = ReadableBy.members

        assert not permits([f"group:{group.pubid}"], Permission.Group.MODERATE)

    def test_creator_has_upsert_permissions(self, group, permits):
        assert permits(group.creator.userid, Permission.Group.UPSERT)

    def test_no_upsert_permission_when_no_creator(
        self, group, permitted_principals_for
    ):
        group.creator = None

        assert not permitted_principals_for(Permission.Group.UPSERT)

    def test_auth_client_with_matching_authority_may_add_members(self, group, permits):
        assert permits(
            ["noise", f"client_authority:{group.authority}"],
            Permission.Group.MEMBER_ADD,
        )

        assert not permits(
            ["noise", "client_authority:DIFFERENT_AUTHORITY"],
            Permission.Group.MEMBER_ADD,
        )

    def test_user_with_authority_may_not_add_members(self, group, permits):
        assert not permits(
            ["noise", f"authority:{group.authority}"], Permission.Group.MEMBER_ADD
        )

    def test_world_readable_and_flaggable(self, group, permits):
        group.readable_by = ReadableBy.world

        assert permits([security.Everyone], Permission.Group.READ)
        assert permits([security.Everyone], Permission.Group.MEMBER_READ)
        assert permits([security.Authenticated], Permission.Group.FLAG)
        assert not permits([security.Everyone], Permission.Group.FLAG)

    def test_members_readable_and_flaggable(self, group, permits):
        group.readable_by = ReadableBy.members

        assert permits([f"group:{group.pubid}"], Permission.Group.READ)
        assert permits([f"group:{group.pubid}"], Permission.Group.MEMBER_READ)
        assert permits([f"group:{group.pubid}"], Permission.Group.FLAG)

    def test_not_readable(self, group, permits):
        group.readable_by = None

        assert not permits(
            [security.Everyone, f"group:{group.pubid}"], Permission.Group.READ
        )
        assert not permits(
            [security.Everyone, f"group:{group.pubid}"], Permission.Group.MEMBER_READ
        )
        assert not permits(
            [security.Authenticated, f"group:{group.pubid}"], Permission.Group.FLAG
        )

    @pytest.mark.parametrize(
        "readable_by", (ReadableBy.world, ReadableBy.members, None)
    )
    def test_the_client_authority_can_always_read(self, group, permits, readable_by):
        group.readable_by = readable_by

        assert permits([f"client_authority:{group.authority}"], Permission.Group.READ)
        assert permits(
            [f"client_authority:{group.authority}"], Permission.Group.MEMBER_READ
        )

    def test_creator_has_admin_permission(self, group, permits):
        assert permits(group.creator.userid, Permission.Group.ADMIN)

    def test_auth_client_with_matching_authority_has_admin_permission(
        self, group, permits
    ):
        assert permits(
            ["noise", f"client_authority:{group.authority}"], Permission.Group.ADMIN
        )
        assert not permits(
            ["noise", "client_authority:DIFFERENT_AUTHORITY"], Permission.Group.ADMIN
        )

    def test_admin_allowed_only_for_authority_when_no_creator(self, group, permits):
        group.creator = None

        assert permits(
            ["noise", f"client_authority:{group.authority}"], Permission.Group.ADMIN
        )

    def test_staff_user_has_admin_permission_on_any_group(self, group, permits):
        assert permits(["noise", role.Staff], Permission.Group.ADMIN)

    def test_admin_user_has_admin_permission_on_any_group(self, group, permits):
        assert permits(["noise", role.Admin], Permission.Group.ADMIN)

    def test_fallback_is_deny_all(self, group, permits):
        assert not permits([security.Everyone], "non_existant_permission")

    @pytest.fixture
    def permits(self, group):
        def permits(principals, permission):
            class ACLCarrier:
                def __acl__(self):
                    return list(ACL.for_group(group))

            return ACLAuthorizationPolicy().permits(
                ACLCarrier(), principals, permission
            )

        return permits

    @pytest.fixture
    def permitted_principals_for(self, group):
        def permitted_principals_for(permission):
            class ACLCarrier:
                def __acl__(self):
                    return list(ACL.for_group(group))

            return ACLAuthorizationPolicy().principals_allowed_by_permission(
                ACLCarrier(), permission
            )

        return permitted_principals_for

    @pytest.fixture
    def group(self, factories):
        return factories.Group.create(creator=factories.User.create())
