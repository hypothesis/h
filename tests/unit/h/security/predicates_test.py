from unittest.mock import sentinel

import pytest

from h.models.group import (
    GroupMembership,
    GroupMembershipRoles,
    JoinableBy,
    ReadableBy,
    WriteableBy,
)
from h.security import Identity, predicates
from h.security.identity import LongLivedGroup, LongLivedMembership
from h.traversal import AnnotationContext, GroupMembershipContext, UserContext
from h.traversal.group import GroupContext


class TestIdentityPredicates:
    def test_authenticated(self, identity):
        assert predicates.authenticated(identity, sentinel.context) == identity
        assert predicates.authenticated(None, sentinel.context) is None

    def test_authenticated_user(self, identity):
        assert (
            predicates.authenticated_user(identity, sentinel.context) == identity.user
        )

    def test_user_is_staff(self, identity):
        identity.user.staff = sentinel.is_staff

        assert (
            predicates.user_is_staff(identity, sentinel.context) == identity.user.staff
        )

    def test_user_is_admin(self, identity):
        identity.user.staff = sentinel.is_admin

        assert predicates.user_is_staff(identity, sentinel.context) == sentinel.is_admin

    def test_authenticated_client(self, identity):
        assert (
            predicates.authenticated_client(identity, sentinel.context)
            == identity.auth_client
        )

    @pytest.mark.parametrize(
        "authority,is_lms",
        (
            ("lms.hypothes.is", True),
            ("lms.other.hypothes.is", True),
            ("other.hypothes.is", False),
            ("lms.other", False),
        ),
    )
    def test_authenticated_client_is_lms(self, identity, authority, is_lms):
        identity.auth_client.authority = authority

        result = predicates.authenticated_client_is_lms(identity, sentinel.context)

        assert result == is_lms


class TestUserPredicates:
    def test_user_found(self, user_context, annotation_context):
        assert not predicates.user_found(sentinel.identity, annotation_context)
        assert not predicates.user_found(sentinel.identity, UserContext(user=None))
        assert predicates.user_found(sentinel.identity, user_context)

    @pytest.mark.parametrize("context_authority", ("auth_client_authority", "other"))
    def test_user_authority_matches_authenticated_client(
        self, identity, user_context, context_authority
    ):
        identity.auth_client.authority = "auth_client_authority"
        user_context.user.authority = context_authority

        result = predicates.user_authority_matches_authenticated_client(
            identity, user_context
        )

        assert bool(result) == bool(context_authority == "auth_client_authority")


class TestAnnotationPredicates:
    def test_annotation_found(self, user_context, annotation_context):
        assert not predicates.annotation_found(sentinel.identity, user_context)
        assert not predicates.annotation_found(
            sentinel.identity, AnnotationContext(annotation=None)
        )
        assert predicates.annotation_found(sentinel.identity, annotation_context)

    def test_annotation_shared(self, annotation_context):
        annotation_context.annotation.shared = sentinel.is_shared

        assert (
            predicates.annotation_shared(sentinel.identity, annotation_context)
            == annotation_context.annotation.shared
        )

    @pytest.mark.parametrize("is_shared", (True, False))
    def test_annotation_not_shared(self, annotation_context, is_shared):
        annotation_context.annotation.shared = is_shared

        result = predicates.annotation_not_shared(sentinel.identity, annotation_context)

        assert result is not is_shared

    @pytest.mark.parametrize("is_deleted", (True, False))
    def test_annotation_live(self, annotation_context, is_deleted):
        annotation_context.annotation.deleted = is_deleted

        result = predicates.annotation_live(sentinel.identity, annotation_context)

        assert result is not is_deleted


class TestGroupPredicates:
    def test_group_found(self, annotation_context, group_context, user_context):
        assert not predicates.group_found(sentinel.identity, user_context)
        assert not predicates.group_found(sentinel.identity, GroupContext(group=None))
        # Annotations have a group
        assert predicates.group_found(sentinel.identity, annotation_context)
        assert predicates.group_found(sentinel.identity, group_context)

    @pytest.mark.parametrize("writable_by", WriteableBy)
    def test_group_writable_by_members(self, group_context, writable_by):
        group_context.group.writeable_by = writable_by

        result = predicates.group_writable_by_members(sentinel.identity, group_context)

        assert result == (writable_by == WriteableBy.members)

    @pytest.mark.parametrize("writable_by", WriteableBy)
    def test_group_writable_by_authority(self, group_context, writable_by):
        group_context.group.writeable_by = writable_by

        result = predicates.group_writable_by_authority(
            sentinel.identity, group_context
        )

        assert result == (writable_by == WriteableBy.authority)

    @pytest.mark.parametrize("readable_by", ReadableBy)
    def test_group_readable_by_world(self, group_context, readable_by):
        group_context.group.readable_by = readable_by

        result = predicates.group_readable_by_world(sentinel.identity, group_context)

        assert result == (readable_by == ReadableBy.world)

    @pytest.mark.parametrize("readable_by", ReadableBy)
    def test_group_readable_by_members(self, group_context, readable_by):
        group_context.group.readable_by = readable_by

        result = predicates.group_readable_by_members(sentinel.identity, group_context)

        assert result == (readable_by == ReadableBy.members)

    @pytest.mark.parametrize("joinable_by", JoinableBy)
    def test_group_joinable_by_authority(self, group_context, joinable_by):
        group_context.group.joinable_by = joinable_by

        result = predicates.group_joinable_by_authority(
            sentinel.identity, group_context
        )

        assert result == (joinable_by == JoinableBy.authority)

    def test_group_created_by_user(self, identity, group_context, factories):
        group_context.group.creator = None
        assert not predicates.group_created_by_user(identity, group_context)

        group_context.group.creator = factories.User.build(id="different_user")
        assert not predicates.group_created_by_user(identity, group_context)

        group_context.group.creator.id = identity.user.id
        assert predicates.group_created_by_user(identity, group_context)

    @pytest.mark.parametrize(
        "role,expected_result",
        [
            (GroupMembershipRoles.OWNER, True),
            (GroupMembershipRoles.ADMIN, False),
            (GroupMembershipRoles.MODERATOR, False),
            (GroupMembershipRoles.MEMBER, False),
            (None, False),
        ],
    )
    def test_group_has_user_as_owner(self, role, expected_result, factories):
        user = factories.User(
            # Make the test user a member of some other groups to make sure these don't confuse the code.
            memberships=[
                GroupMembership(
                    group=factories.Group.build(), roles=[GroupMembershipRoles.OWNER]
                ),
                GroupMembership(
                    group=factories.Group.build(), roles=[GroupMembershipRoles.ADMIN]
                ),
                GroupMembership(
                    group=factories.Group.build(),
                    roles=[GroupMembershipRoles.MODERATOR],
                ),
                GroupMembership(
                    group=factories.Group.build(), roles=[GroupMembershipRoles.MEMBER]
                ),
            ]
        )
        group = factories.Group(
            # Add some other members to the test group to make sure these don't confuse the code.
            memberships=[
                GroupMembership(
                    user=factories.User(), roles=[GroupMembershipRoles.OWNER]
                ),
                GroupMembership(
                    user=factories.User(), roles=[GroupMembershipRoles.ADMIN]
                ),
                GroupMembership(
                    user=factories.User(), roles=[GroupMembershipRoles.MODERATOR]
                ),
                GroupMembership(
                    user=factories.User(), roles=[GroupMembershipRoles.MEMBER]
                ),
            ]
        )
        if role:
            # Make the test user a member of the test group with `role`.
            group.memberships.append(GroupMembership(user=user, roles=[role]))
        identity = Identity.from_models(user)
        context = GroupContext(group)

        assert predicates.group_has_user_as_owner(identity, context) == expected_result

    @pytest.mark.parametrize(
        "role,expected_result",
        [
            (GroupMembershipRoles.OWNER, False),
            (GroupMembershipRoles.ADMIN, True),
            (GroupMembershipRoles.MODERATOR, False),
            (GroupMembershipRoles.MEMBER, False),
            (None, False),
        ],
    )
    def test_group_has_user_as_admin(self, role, expected_result, factories):
        user = factories.User(
            # Make the test user a member of some other groups to make sure these don't confuse the code.
            memberships=[
                GroupMembership(
                    group=factories.Group.build(), roles=[GroupMembershipRoles.OWNER]
                ),
                GroupMembership(
                    group=factories.Group.build(), roles=[GroupMembershipRoles.ADMIN]
                ),
                GroupMembership(
                    group=factories.Group.build(),
                    roles=[GroupMembershipRoles.MODERATOR],
                ),
                GroupMembership(
                    group=factories.Group.build(), roles=[GroupMembershipRoles.MEMBER]
                ),
            ]
        )
        group = factories.Group(
            # Add some other members to the test group to make sure these don't confuse the code.
            memberships=[
                GroupMembership(
                    user=factories.User(), roles=[GroupMembershipRoles.OWNER]
                ),
                GroupMembership(
                    user=factories.User(), roles=[GroupMembershipRoles.ADMIN]
                ),
                GroupMembership(
                    user=factories.User(), roles=[GroupMembershipRoles.MODERATOR]
                ),
                GroupMembership(
                    user=factories.User(), roles=[GroupMembershipRoles.MEMBER]
                ),
            ]
        )
        if role:
            # Make the test user a member of the test group with `role`.
            group.memberships.append(GroupMembership(user=user, roles=[role]))
        identity = Identity.from_models(user)
        context = GroupContext(group)

        assert predicates.group_has_user_as_admin(identity, context) == expected_result

    @pytest.mark.parametrize(
        "role,expected_result",
        [
            (GroupMembershipRoles.OWNER, False),
            (GroupMembershipRoles.ADMIN, False),
            (GroupMembershipRoles.MODERATOR, True),
            (GroupMembershipRoles.MEMBER, False),
            (None, False),
        ],
    )
    def test_group_has_user_as_moderator(self, role, expected_result, factories):
        user = factories.User(
            # Make the test user a member of some other groups to make sure these don't confuse the code.
            memberships=[
                GroupMembership(
                    group=factories.Group.build(), roles=[GroupMembershipRoles.OWNER]
                ),
                GroupMembership(
                    group=factories.Group.build(), roles=[GroupMembershipRoles.ADMIN]
                ),
                GroupMembership(
                    group=factories.Group.build(),
                    roles=[GroupMembershipRoles.MODERATOR],
                ),
                GroupMembership(
                    group=factories.Group.build(), roles=[GroupMembershipRoles.MEMBER]
                ),
            ]
        )
        group = factories.Group(
            # Add some other members to the test group to make sure these don't confuse the code.
            memberships=[
                GroupMembership(
                    user=factories.User(), roles=[GroupMembershipRoles.OWNER]
                ),
                GroupMembership(
                    user=factories.User(), roles=[GroupMembershipRoles.ADMIN]
                ),
                GroupMembership(
                    user=factories.User(), roles=[GroupMembershipRoles.MODERATOR]
                ),
                GroupMembership(
                    user=factories.User(), roles=[GroupMembershipRoles.MEMBER]
                ),
            ]
        )
        if role:
            # Make the test user a member of the test group with `role`.
            group.memberships.append(GroupMembership(user=user, roles=[role]))
        identity = Identity.from_models(user)
        context = GroupContext(group)

        assert (
            predicates.group_has_user_as_moderator(identity, context) == expected_result
        )

    @pytest.mark.parametrize(
        "role,expected_result",
        [
            (GroupMembershipRoles.OWNER, True),
            (GroupMembershipRoles.ADMIN, True),
            (GroupMembershipRoles.MODERATOR, True),
            (GroupMembershipRoles.MEMBER, True),
            (None, False),
        ],
    )
    def test_group_has_user_as_member(self, role, expected_result, factories):
        user = factories.User(
            # Make the test user a member of some other groups to make sure these don't confuse the code.
            memberships=[
                GroupMembership(
                    group=factories.Group.build(), roles=[GroupMembershipRoles.OWNER]
                ),
                GroupMembership(
                    group=factories.Group.build(), roles=[GroupMembershipRoles.ADMIN]
                ),
                GroupMembership(
                    group=factories.Group.build(),
                    roles=[GroupMembershipRoles.MODERATOR],
                ),
                GroupMembership(
                    group=factories.Group.build(), roles=[GroupMembershipRoles.MEMBER]
                ),
            ]
        )
        group = factories.Group(
            # Add some other members to the test group to make sure these don't confuse the code.
            memberships=[
                GroupMembership(
                    user=factories.User(), roles=[GroupMembershipRoles.OWNER]
                ),
                GroupMembership(
                    user=factories.User(), roles=[GroupMembershipRoles.ADMIN]
                ),
                GroupMembership(
                    user=factories.User(), roles=[GroupMembershipRoles.MODERATOR]
                ),
                GroupMembership(
                    user=factories.User(), roles=[GroupMembershipRoles.MEMBER]
                ),
            ]
        )
        if role:
            # Make the test user a member of the test group with `role`.
            group.memberships.append(GroupMembership(user=user, roles=[role]))
        identity = Identity.from_models(user)
        context = GroupContext(group)

        assert predicates.group_has_user_as_member(identity, context) == expected_result

    @pytest.mark.parametrize("context_authority", ("user_authority", "other"))
    def test_group_matches_user_authority(
        self, group_context, identity, context_authority
    ):
        identity.user.authority = "user_authority"
        group_context.group.authority = context_authority

        result = predicates.group_matches_user_authority(identity, group_context)

        assert bool(result) == bool(context_authority == "user_authority")

    @pytest.mark.parametrize("context_authority", ("auth_client_authority", "other"))
    def test_group_matches_authenticated_client_authority(
        self, group_context, identity, context_authority
    ):
        identity.auth_client.authority = "auth_client_authority"
        group_context.group.authority = context_authority

        result = predicates.group_matches_authenticated_client_authority(
            identity, group_context
        )

        assert bool(result) == bool(context_authority == "auth_client_authority")

    @pytest.fixture
    def group_context(self, factories):
        return GroupContext(group=factories.Group.build())


class TestGroupMemberRemove:
    @pytest.mark.parametrize(
        "authenticated_users_role,target_users_role,expected_result",
        [
            # Only owners can remove other owners.
            (GroupMembershipRoles.OWNER, GroupMembershipRoles.OWNER, True),
            (GroupMembershipRoles.ADMIN, GroupMembershipRoles.OWNER, False),
            (GroupMembershipRoles.MODERATOR, GroupMembershipRoles.OWNER, False),
            (GroupMembershipRoles.MEMBER, GroupMembershipRoles.OWNER, False),
            # Only owners can remove admins.
            (GroupMembershipRoles.OWNER, GroupMembershipRoles.ADMIN, True),
            (GroupMembershipRoles.ADMIN, GroupMembershipRoles.ADMIN, False),
            (GroupMembershipRoles.MODERATOR, GroupMembershipRoles.ADMIN, False),
            (GroupMembershipRoles.MEMBER, GroupMembershipRoles.ADMIN, False),
            # Owners and admins can remove moderators.
            (GroupMembershipRoles.OWNER, GroupMembershipRoles.MODERATOR, True),
            (GroupMembershipRoles.ADMIN, GroupMembershipRoles.MODERATOR, True),
            (GroupMembershipRoles.MODERATOR, GroupMembershipRoles.MODERATOR, False),
            (GroupMembershipRoles.MEMBER, GroupMembershipRoles.MODERATOR, False),
            # Owners, admins and moderators can remove members.
            (GroupMembershipRoles.OWNER, GroupMembershipRoles.MEMBER, True),
            (GroupMembershipRoles.ADMIN, GroupMembershipRoles.MEMBER, True),
            (GroupMembershipRoles.MODERATOR, GroupMembershipRoles.MEMBER, True),
            (GroupMembershipRoles.MEMBER, GroupMembershipRoles.MEMBER, False),
            # Non-members can't remove anyone.
            (None, GroupMembershipRoles.OWNER, False),
            (None, GroupMembershipRoles.ADMIN, False),
            (None, GroupMembershipRoles.MEMBER, False),
            (None, GroupMembershipRoles.MODERATOR, False),
        ],
    )
    def test_it(
        self,
        identity,
        context,
        group,
        target_users_role,
        authenticated_users_role,
        expected_result,
    ):
        if authenticated_users_role:
            identity.user.memberships.append(
                LongLivedMembership(
                    group=LongLivedGroup.from_model(group),
                    user=identity.user,
                    roles=[authenticated_users_role],
                )
            )
        context.membership.roles = [target_users_role]

        assert predicates.group_member_remove(identity, context) == expected_result

    @pytest.mark.parametrize(
        "role",
        [
            GroupMembershipRoles.OWNER,
            GroupMembershipRoles.ADMIN,
            GroupMembershipRoles.MODERATOR,
            GroupMembershipRoles.MEMBER,
        ],
    )
    def test_any_member_can_remove_themselves_from_a_group(
        self, identity, context, role, group
    ):
        identity.user.userid = context.user.userid
        identity.user.memberships.append(
            LongLivedMembership(
                group=LongLivedGroup.from_model(group),
                user=identity.user,
                roles=[role],
            )
        )
        context.membership.roles = [role]

        assert predicates.group_member_remove(identity, context) is True

    @pytest.fixture
    def authenticated_user(self, db_session, authenticated_user, factories):
        # Make the authenticated user a member of a *different* group,
        # to make sure that unrelated memberships don't accidentally allow or
        # deny permissions.
        db_session.add(
            GroupMembership(
                user=authenticated_user,
                group=factories.Group(),
                roles=[GroupMembershipRoles.OWNER],
            )
        )

        return authenticated_user

    @pytest.fixture
    def group(self, db_session, factories):
        group = factories.Group()

        # Make a *different* user a member of the target group
        # to make sure that unrelated memberships don't accidentally allow or
        # deny permissions.
        db_session.add(
            GroupMembership(
                group=group, user=factories.User(), roles=[GroupMembershipRoles.OWNER]
            )
        )

        return group

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def context(self, group, user):
        return GroupMembershipContext(
            group=group, user=user, membership=GroupMembership(group=group, user=user)
        )


class TestResolvePredicates:
    @pytest.mark.parametrize(
        "clause,expansion",
        (
            ((predicates.authenticated,), [predicates.authenticated]),
            (
                (predicates.authenticated, predicates.authenticated),
                [predicates.authenticated],
            ),
            (
                (predicates.authenticated_user,),
                [predicates.authenticated, predicates.authenticated_user],
            ),
            (
                # This has a two requires
                (predicates.group_has_user_as_member,),
                [
                    predicates.authenticated,
                    predicates.authenticated_user,
                    predicates.group_found,
                    predicates.group_has_user_as_member,
                ],
            ),
            (
                (predicates.user_is_staff, predicates.user_is_admin),
                [
                    # These are very similar predicates, this is here to test
                    # duplicate removal
                    predicates.authenticated,
                    predicates.authenticated_user,
                    predicates.user_is_staff,
                    predicates.user_is_admin,
                ],
            ),
        ),
    )
    def test_it(self, clause, expansion):
        result = predicates.resolve_predicates({"permission": [clause]})

        assert result == {"permission": [expansion]}


@pytest.fixture
def annotation_context(factories):
    return AnnotationContext(
        annotation=factories.Annotation.build(group=factories.Group.build())
    )


@pytest.fixture
def user_context(factories):
    return UserContext(user=factories.User.build(id="userid"))


@pytest.fixture
def authenticated_user(factories):
    return factories.User.build()


@pytest.fixture
def identity(authenticated_user, factories):
    return Identity.from_models(
        user=authenticated_user, auth_client=factories.AuthClient.build()
    )
