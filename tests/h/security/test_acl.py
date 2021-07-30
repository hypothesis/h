import functools

import pytest
from pyramid import security
from pyramid.authorization import ACLAuthorizationPolicy

from h.auth import role
from h.models.group import JoinableBy, ReadableBy, WriteableBy
from h.security.acl import ACL
from h.security.permissions import Permission


class TestACLForUser:
    @pytest.mark.parametrize(
        "principal_template,is_permitted",
        (
            # The right client authority has permissions
            ("client_authority:{user.authority}", True),
            ("client_authority:DIFFERENT", False),
            # User's don't by just being in the authority
            ("authority:{user.authority}", False),
        ),
    )
    @pytest.mark.parametrize(
        "permission", (Permission.User.UPDATE, Permission.User.READ)
    )
    def test_it(self, permits, user, principal_template, permission, is_permitted):
        principal = principal_template.format(user=user)
        assert bool(permits([principal, "some_noise"], permission)) == is_permitted

    @pytest.fixture
    def permits(self, permits, user):
        return functools.partial(permits, ACL.for_user(user))

    @pytest.fixture
    def user(self, factories):
        return factories.User.create()


class TestACLForGroup:
    def test_authority_joinable(self, group, permits):
        group.joinable_by = JoinableBy.authority

        assert permits([f"authority:{group.authority}"], Permission.Group.JOIN)
        assert not permits(["authority:DIFFERENT_AUTHORITY"], Permission.Group.JOIN)

    def test_not_joinable(self, group, permits):
        group.joinable_by = None

        assert not permits([f"authority:{group.authority}"], Permission.Group.JOIN)

    def test_authority_writeable(self, group, permits):
        group.writeable_by = WriteableBy.authority

        assert permits([f"authority:{group.authority}"], Permission.Group.WRITE)

    def test_members_writeable(self, group, permits):
        group.writeable_by = WriteableBy.members

        assert permits([f"group:{group.pubid}"], Permission.Group.WRITE)

    def test_not_writeable(self, group, permitted_principals_for):
        group.writeable_by = None

        assert not permitted_principals_for(Permission.Group.WRITE)

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

    def test_auth_client_with_matching_authority_may_add_members(
        self, group, permitted_principals_for
    ):
        assert permitted_principals_for(Permission.Group.MEMBER_ADD) == {
            f"client_authority:{group.authority}"
        }

    def test_auth_client_with_matching_authority_has_admin_permission(
        self, group, permits
    ):
        assert permits([f"client_authority:{group.authority}"], Permission.Group.ADMIN)
        assert not permits(
            ["client_authority:DIFFERENT_AUTHORITY"], Permission.Group.ADMIN
        )

    def test_staff_user_has_admin_permission_on_any_group(self, group, permits):
        assert permits([role.Staff], Permission.Group.ADMIN)

    def test_admin_user_has_admin_permission_on_any_group(self, group, permits):
        assert permits([role.Admin], Permission.Group.ADMIN)

    @pytest.mark.parametrize("readable_by", (ReadableBy.members, ReadableBy.world))
    def test_creator_permissions(
        self, group, permitted_principals_for, permits, readable_by
    ):
        group.readable_by = readable_by

        assert permits(group.creator.userid, Permission.Group.ADMIN)
        assert permits(group.creator.userid, Permission.Group.UPSERT)
        assert permitted_principals_for(Permission.Group.MODERATE) == {
            group.creator.userid
        }

    def test_no_creator_permissions_without_creator(
        self, group, permitted_principals_for
    ):
        group.creator = None

        assert not permitted_principals_for(Permission.Group.MODERATE)
        assert not permitted_principals_for(Permission.Group.UPSERT)

    def test_fallback_is_deny_all(self, group, permits):
        assert not permits([security.Everyone], "non_existant_permission")

    @pytest.fixture
    def permits(self, permits, group):
        return functools.partial(permits, ACL.for_group(group))

    @pytest.fixture
    def permitted_principals_for(self, group):
        def permitted_principals_for(permission):
            return ACLAuthorizationPolicy().principals_allowed_by_permission(
                ObjectWithACL(ACL.for_group(group)), permission
            )

        return permitted_principals_for

    @pytest.fixture
    def group(self, factories):
        return factories.Group.create(creator=factories.User.create())


class ObjectWithACL:
    # We can't use a raw list of ACLs with Pyramid's permissions system so we
    # need a small object which has the interface that Pyramid expects in order
    # for it to understand them
    def __init__(self, acl):
        self.__acl__ = acl


@pytest.fixture
def permits():
    def permits(acl_iterable, principals, permission):
        return ACLAuthorizationPolicy().permits(
            ObjectWithACL(acl_iterable), principals, permission
        )

    return permits
