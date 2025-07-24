from unittest.mock import call, sentinel

import pytest

from h.models import GroupMembership, GroupMembershipRoles
from h.security.identity import (
    Identity,
    LongLivedAuthClient,
    LongLivedGroup,
    LongLivedMembership,
    LongLivedUser,
)


class TestLongLivedGroup:
    def test_from_models(self, factories, matchers):
        group = factories.Group.build()

        model = LongLivedGroup.from_model(group)

        assert model == matchers.InstanceOf(
            LongLivedGroup, id=group.id, pubid=group.pubid
        )


class TestLongLivedUser:
    def test_from_model(self, db_session, factories, LongLivedGroup):
        groups = factories.Group.create_batch(size=2)
        user = factories.User(
            memberships=[
                GroupMembership(group=groups[0], roles=[GroupMembershipRoles.MEMBER]),
                GroupMembership(group=groups[1], roles=[GroupMembershipRoles.ADMIN]),
            ]
        )
        LongLivedGroup.from_model.side_effect = [
            sentinel.long_lived_group_1,
            sentinel.long_lived_group_2,
        ]
        db_session.flush()

        model = LongLivedUser.from_model(user)

        assert LongLivedGroup.from_model.call_args_list == [
            call(groups[0]),
            call(groups[1]),
        ]

        assert model == LongLivedUser(
            id=user.id,
            userid=user.userid,
            authority=user.authority,
            admin=user.admin,
            staff=user.staff,
            memberships=[
                LongLivedMembership(
                    group=sentinel.long_lived_group_1,
                    user=model,
                    roles=[GroupMembershipRoles.MEMBER],
                ),
                LongLivedMembership(
                    group=sentinel.long_lived_group_2,
                    user=model,
                    roles=[GroupMembershipRoles.ADMIN],
                ),
            ],
        )

    @pytest.fixture(autouse=True)
    def LongLivedGroup(self, patch):
        return patch("h.security.identity.LongLivedGroup")


class TestLongLivedAuthClient:
    def test_from_models(self, factories, matchers):
        auth_client = factories.AuthClient.build()

        model = LongLivedAuthClient.from_model(auth_client)

        assert model == matchers.InstanceOf(
            LongLivedAuthClient,
            id=auth_client.id,
            authority=auth_client.authority,
        )


class TestIdentity:
    def test_from_models(self, LongLivedUser, LongLivedAuthClient, matchers):
        identity = Identity.from_models(
            user=sentinel.user, auth_client=sentinel.auth_client
        )

        LongLivedUser.from_model.assert_called_once_with(sentinel.user)
        LongLivedAuthClient.from_model.assert_called_once_with(sentinel.auth_client)
        assert identity == matchers.InstanceOf(
            Identity,
            user=LongLivedUser.from_model.return_value,
            auth_client=LongLivedAuthClient.from_model.return_value,
        )

    def test_from_models_with_None(self, LongLivedUser, LongLivedAuthClient, matchers):
        identity = Identity.from_models()

        LongLivedUser.from_model.assert_not_called()
        LongLivedAuthClient.from_model.assert_not_called()

        assert identity == matchers.InstanceOf(Identity, user=None, auth_client=None)

    @pytest.mark.parametrize(
        "identity,authenticated_userid",
        [
            (None, None),
            (Identity(user=None), None),
            (
                Identity(
                    user=LongLivedUser(
                        id=sentinel.id,
                        userid=sentinel.userid,
                        authority=sentinel.authority,
                        staff=False,
                        admin=False,
                    )
                ),
                sentinel.userid,
            ),
        ],
    )
    def test_authenticated_userid(self, identity, authenticated_userid):
        assert Identity.authenticated_userid(identity) == authenticated_userid

    @pytest.fixture(autouse=True)
    def LongLivedUser(self, patch):
        return patch("h.security.identity.LongLivedUser")

    @pytest.fixture(autouse=True)
    def LongLivedAuthClient(self, patch):
        return patch("h.security.identity.LongLivedAuthClient")


class TestGetRoles:
    def test_it(self, identity, group):
        identity.user.memberships.append(
            LongLivedMembership(
                user=identity.user, group=group, roles=[GroupMembershipRoles.MODERATOR]
            ),
        )

        assert identity.get_roles(group) == [GroupMembershipRoles.MODERATOR]

    def test_when_no_membership(self, identity, group):
        assert identity.get_roles(group) == []

    def test_when_no_user(self, identity, group):
        identity.user = None

        assert identity.get_roles(group) == []

    @pytest.fixture
    def identity(self):
        identity = Identity(
            user=LongLivedUser(
                id=sentinel.id,
                userid=sentinel.userid,
                authority=sentinel.authority,
                staff=sentinel.staff,
                admin=sentinel.admin,
            )
        )
        identity.user.memberships = [
            LongLivedMembership(
                user=identity.user,
                group=LongLivedGroup(id=24, pubid="other"),
                roles=[GroupMembershipRoles.MEMBER],
            )
        ]
        return identity

    @pytest.fixture
    def group(self):
        return LongLivedGroup(id=42, pubid="pubid")
