import functools
from unittest.mock import patch

import pytest
from h_matchers import Any
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
    def test_it(self, user_permits, user, principal_template, permission, is_permitted):
        principal = principal_template.format(user=user)
        assert bool(user_permits([principal, "some_noise"], permission)) == is_permitted

    def test_a_user_is_not_required_for_create(self, permits):
        acl_object = ObjectWithACL(ACL.for_user(user=None))

        permits(acl_object, [role.AuthClient], Permission.User.CREATE)

    @pytest.fixture
    def user_permits(self, permits, user):
        return functools.partial(permits, ObjectWithACL(ACL.for_user(user)))

    @pytest.fixture
    def user(self, factories):
        return factories.User.create()


class TestACLForGroup:
    def test_logged_in_users_get_create_permission(
        self, group_permits, no_group_permits
    ):
        assert group_permits([role.User], Permission.Group.CREATE)
        assert not group_permits([], Permission.Group.CREATE)
        assert no_group_permits([role.User], Permission.Group.CREATE)
        assert not no_group_permits([], Permission.Group.CREATE)

    def test_logged_in_users_get_upsert_permission_when_theres_no_group(
        self, no_group_permits
    ):
        assert no_group_permits([role.User], Permission.Group.UPSERT)
        assert not no_group_permits([], Permission.Group.UPSERT)

    def test_authority_joinable(self, group, group_permits):
        group.joinable_by = JoinableBy.authority

        assert group_permits([f"authority:{group.authority}"], Permission.Group.JOIN)
        assert not group_permits(
            ["authority:DIFFERENT_AUTHORITY"], Permission.Group.JOIN
        )

    def test_not_joinable(self, group, group_permits):
        group.joinable_by = None

        assert not group_permits(
            [f"authority:{group.authority}"], Permission.Group.JOIN
        )

    def test_authority_writeable(self, group, group_permits):
        group.writeable_by = WriteableBy.authority

        assert group_permits([f"authority:{group.authority}"], Permission.Group.WRITE)

    def test_members_writeable(self, group, group_permits):
        group.writeable_by = WriteableBy.members

        assert group_permits([f"group:{group.pubid}"], Permission.Group.WRITE)

    def test_not_writeable(self, group, permitted_principals_for):
        group.writeable_by = None

        assert not permitted_principals_for(Permission.Group.WRITE)

    def test_world_readable_and_flaggable(self, group, group_permits):
        group.readable_by = ReadableBy.world

        assert group_permits([security.Everyone], Permission.Group.READ)
        assert group_permits([security.Everyone], Permission.Group.MEMBER_READ)
        assert group_permits([security.Authenticated], Permission.Group.FLAG)
        assert not group_permits([security.Everyone], Permission.Group.FLAG)

    def test_members_readable_and_flaggable(self, group, group_permits):
        group.readable_by = ReadableBy.members

        assert group_permits([f"group:{group.pubid}"], Permission.Group.READ)
        assert group_permits([f"group:{group.pubid}"], Permission.Group.MEMBER_READ)
        assert group_permits([f"group:{group.pubid}"], Permission.Group.FLAG)

    def test_not_readable(self, group, group_permits):
        group.readable_by = None

        assert not group_permits(
            [security.Everyone, f"group:{group.pubid}"], Permission.Group.READ
        )
        assert not group_permits(
            [security.Everyone, f"group:{group.pubid}"], Permission.Group.MEMBER_READ
        )
        assert not group_permits(
            [security.Authenticated, f"group:{group.pubid}"], Permission.Group.FLAG
        )

    @pytest.mark.parametrize(
        "readable_by", (ReadableBy.world, ReadableBy.members, None)
    )
    def test_the_client_authority_can_always_read(
        self, group, group_permits, readable_by
    ):
        group.readable_by = readable_by

        assert group_permits(
            [f"client_authority:{group.authority}"], Permission.Group.READ
        )
        assert group_permits(
            [f"client_authority:{group.authority}"], Permission.Group.MEMBER_READ
        )

    def test_auth_client_with_matching_authority_may_add_members(
        self, group, permitted_principals_for
    ):
        assert permitted_principals_for(Permission.Group.MEMBER_ADD) == {
            f"client_authority:{group.authority}"
        }

    def test_auth_client_with_matching_authority_has_admin_permission(
        self, group, group_permits
    ):
        assert group_permits(
            [f"client_authority:{group.authority}"], Permission.Group.ADMIN
        )
        assert not group_permits(
            ["client_authority:DIFFERENT_AUTHORITY"], Permission.Group.ADMIN
        )

    def test_staff_user_has_admin_permission_on_any_group(self, group, group_permits):
        assert group_permits([role.Staff], Permission.Group.ADMIN)

    def test_admin_user_has_admin_permission_on_any_group(self, group, group_permits):
        assert group_permits([role.Admin], Permission.Group.ADMIN)

    @pytest.mark.parametrize("readable_by", (ReadableBy.members, ReadableBy.world))
    def test_creator_permissions(
        self, group, permitted_principals_for, group_permits, readable_by
    ):
        group.readable_by = readable_by

        assert group_permits(group.creator.userid, Permission.Group.ADMIN)
        assert group_permits(group.creator.userid, Permission.Group.UPSERT)
        assert permitted_principals_for(Permission.Group.MODERATE) == {
            group.creator.userid
        }

    def test_no_creator_permissions_without_creator(
        self, group, permitted_principals_for
    ):
        group.creator = None

        assert not permitted_principals_for(Permission.Group.MODERATE)
        assert not permitted_principals_for(Permission.Group.UPSERT)

    def test_fallback_is_deny_all(self, group, group_permits):
        assert not group_permits([security.Everyone], "non_existant_permission")

    @pytest.fixture
    def no_group_permits(self, permits):
        return functools.partial(permits, ObjectWithACL(ACL.for_group(None)))

    @pytest.fixture
    def group_permits(self, permits, group):
        return functools.partial(permits, ObjectWithACL(ACL.for_group(group)))

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


class TestACLForAnnotation:
    def test_it_grants_create_to_authenticated_users(self, permits):
        acl = ACL.for_annotation(None)  # Doesn't require an annotation

        assert permits(
            ObjectWithACL(acl), [security.Authenticated], Permission.Annotation.CREATE
        )
        assert not permits(ObjectWithACL(acl), [], Permission.Annotation.CREATE)

    def test_it_allows_read_realtime_on_delete(self, annotation, anno_permits):
        annotation.deleted = True

        # Users should normally have permissions to read their own annotations
        # so we'll use that as an example
        assert anno_permits(
            [annotation.userid], Permission.Annotation.READ_REALTIME_UPDATES
        )
        assert not anno_permits([annotation.userid], Permission.Annotation.READ)

    def test_it_allows_the_user_to_always_update_and_delete_their_own(
        self, annotation, anno_permits
    ):
        anno_permits([annotation.userid], Permission.Annotation.UPDATE)
        anno_permits([annotation.userid], Permission.Annotation.DELETE)

    def test_it_gives_non_shared_permissions_go_to_the_user(
        self, annotation, anno_permits
    ):
        annotation.shared = False

        anno_permits([annotation.userid], Permission.Annotation.READ)
        anno_permits([annotation.userid], Permission.Annotation.FLAG)

    @pytest.mark.parametrize(
        "group_permission,annotation_permission",
        (
            (Permission.Group.FLAG, Permission.Annotation.FLAG),
            (Permission.Group.MODERATE, Permission.Annotation.MODERATE),
            (Permission.Group.READ, Permission.Annotation.READ),
            (Permission.Group.READ, Permission.Annotation.READ_REALTIME_UPDATES),
        ),
    )
    def test_it_mirrors_permissions_from_the_group_for_shared_annotations(
        self,
        annotation,
        group,
        anno_permits,
        group_permission,
        annotation_permission,
        for_group,
    ):
        annotation.shared = True
        for_group.return_value = [
            (security.Allow, "principal_1", group_permission),
            (security.Allow, "principal_2", group_permission),
        ]

        anno_permits(["principal_1"], annotation_permission)
        anno_permits(["principal_2"], annotation_permission)

        # This is called a bunch of times right now, we don't need to get too
        # specific. We can tell it's doing it's job of passing on the ACLs by
        # the assertions above
        for_group.assert_called_with(group)

    def test_it_with_a_shared_annotation_with_no_group(self, annotation, anno_permits):
        annotation.shared = True
        annotation.group = None

        acl = ACL.for_annotation(annotation)

        assert (security.Allow, Any(), Permission.Annotation.FLAG) not in acl
        assert (security.Allow, Any(), Permission.Annotation.MODERATE) not in acl

    @pytest.fixture
    def for_group(self):
        with patch.object(ACL, "for_group") as for_group:
            yield for_group

    @pytest.fixture
    def anno_permits(self, permits, annotation):
        return functools.partial(permits, ObjectWithACL(ACL.for_annotation(annotation)))

    @pytest.fixture
    def annotation(self, factories, group):
        return factories.Annotation(groupid=group.pubid)

    @pytest.fixture
    def group(self, factories):
        return factories.Group()


class ObjectWithACL:
    # We can't use a raw list of ACLs with Pyramid's permissions system so we
    # need a small object which has the interface that Pyramid expects in order
    # for it to understand them
    def __init__(self, acl):
        self.__acl__ = acl


@pytest.fixture
def permits():
    return ACLAuthorizationPolicy().permits
