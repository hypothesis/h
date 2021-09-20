from unittest.mock import sentinel

import pytest

from h.models.group import JoinableBy, ReadableBy, WriteableBy
from h.security import Identity, predicates
from h.traversal import AnnotationContext, UserContext
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

    def test_group_not_found(self, annotation_context, group_context, user_context):
        assert predicates.group_not_found(sentinel.identity, user_context)
        assert predicates.group_not_found(sentinel.identity, GroupContext(group=None))
        # Annotations have a group
        assert not predicates.group_not_found(sentinel.identity, annotation_context)
        assert not predicates.group_not_found(sentinel.identity, group_context)

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

    @pytest.mark.parametrize("matching", (True, False))
    def test_group_has_user_as_member(
        self, group_context, identity, factories, matching
    ):
        # Note we don't use the same literal objects here. It's important
        # that we test based on the values not Python equality as the objects
        # are detached in the WS and don't evaluate as equal
        identity.user.groups = [factories.Group.build(id=i) for i in range(3)]
        group_context.group = factories.Group.build(id=1 if matching else 100)

        assert predicates.group_has_user_as_member(identity, group_context) == matching

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
def identity(factories):
    return Identity.from_models(
        user=factories.User.build(), auth_client=factories.AuthClient.build()
    )
