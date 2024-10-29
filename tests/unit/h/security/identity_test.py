from unittest.mock import sentinel

import pytest
from h_matchers import Any

from h.models import GroupMembership
from h.security.identity import (
    Identity,
    LongLivedAuthClient,
    LongLivedGroup,
    LongLivedUser,
)


class TestLongLivedGroup:
    def test_from_models(self, factories):
        group = factories.Group.build()

        model = LongLivedGroup.from_model(group)

        assert model == Any.instance_of(LongLivedGroup).with_attrs(
            {"id": group.id, "pubid": group.pubid}
        )


class TestLongLivedUser:
    def test_from_models(self, factories, LongLivedGroup):
        group = factories.Group.build()
        user = factories.User.build(memberships=[GroupMembership(group=group)])

        model = LongLivedUser.from_model(user)

        LongLivedGroup.from_model.assert_called_once_with(group)
        assert model == Any.instance_of(LongLivedUser).with_attrs(
            {
                "id": user.id,
                "userid": user.userid,
                "authority": user.authority,
                "admin": user.admin,
                "staff": user.staff,
                "groups": [LongLivedGroup.from_model.return_value],
            }
        )

    @pytest.fixture(autouse=True)
    def LongLivedGroup(self, patch):
        return patch("h.security.identity.LongLivedGroup")


class TestLongLivedAuthClient:
    def test_from_models(self, factories):
        auth_client = factories.AuthClient.build()

        model = LongLivedAuthClient.from_model(auth_client)

        assert model == Any.instance_of(LongLivedAuthClient).with_attrs(
            {"id": auth_client.id, "authority": auth_client.authority}
        )


class TestIdentity:
    def test_from_models(self, LongLivedUser, LongLivedAuthClient):
        identity = Identity.from_models(
            user=sentinel.user, auth_client=sentinel.auth_client
        )

        LongLivedUser.from_model.assert_called_once_with(sentinel.user)
        LongLivedAuthClient.from_model.assert_called_once_with(sentinel.auth_client)
        assert identity == Any.instance_of(Identity).with_attrs(
            {
                "user": LongLivedUser.from_model.return_value,
                "auth_client": LongLivedAuthClient.from_model.return_value,
            }
        )

    def test_from_models_with_None(self, LongLivedUser, LongLivedAuthClient):
        identity = Identity.from_models()

        LongLivedUser.from_model.assert_not_called()
        LongLivedAuthClient.from_model.assert_not_called()

        assert identity == Any.instance_of(Identity).with_attrs(
            {"user": None, "auth_client": None}
        )

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
                        groups=[],
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
