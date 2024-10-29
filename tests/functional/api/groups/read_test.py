import base64

import pytest

from h.models import GroupMembership
from h.models.auth_client import GrantType


class TestReadGroups:
    # TODO: In subsequent versions of the API, this should really be a group
    # search endpoint and should have its own functional test module

    def test_it_returns_world_group(self, app):
        # world group is auto-added in tests
        res = app.get("/api/groups")

        assert res.status_code == 200
        assert res.json[0]["id"] == "__world__"

    def test_it_returns_private_groups_along_with_world_groups(
        self, app, factories, db_session, user_with_token, token_auth_header
    ):
        user, _ = user_with_token
        group1 = factories.Group(memberships=[GroupMembership(user=user)])
        group2 = factories.Group(memberships=[GroupMembership(user=user)])
        db_session.commit()

        res = app.get("/api/groups", headers=token_auth_header)

        groupids = [group["id"] for group in res.json]
        assert "__world__" in groupids
        assert group1.pubid in groupids
        assert group2.pubid in groupids

    def test_it_overrides_authority_param_with_user_authority(
        self, app, factories, db_session, user_with_token, token_auth_header
    ):
        user, _ = user_with_token
        group1 = factories.Group(
            authority=user.authority, memberships=[GroupMembership(user=user)]
        )
        db_session.commit()

        res = app.get("/api/groups?authority=whatever.com", headers=token_auth_header)

        groupids = [group["id"] for group in res.json]
        # It still returns the groups from the user's authority
        assert group1.pubid in groupids

    def test_it_expands_scope_if_requested(self, app):
        res = app.get("/api/groups?expand=scopes")

        assert res.status_code == 200
        assert "scopes" in res.json[0]


class TestReadGroup:
    def test_it_returns_http_200_for_world_readable_group_pubid(
        self, app, factories, db_session
    ):
        group = factories.OpenGroup()
        db_session.commit()

        res = app.get("/api/groups/{pubid}".format(pubid=group.pubid))

        assert res.status_code == 200

        data = res.json
        assert "id" in data

    def test_it_returns_http_200_for_world_readable_groupid(
        self, app, factories, db_session
    ):
        factories.OpenGroup(authority_provided_id="foo", authority="bar.com")
        db_session.commit()
        res = app.get("/api/groups/group:foo@bar.com")

        assert res.status_code == 200

    def test_it_returns_http_404_for_private_group_no_authentication(
        self, app, factories, db_session
    ):
        group = factories.Group()
        db_session.commit()

        res = app.get(
            "/api/groups/{pubid}".format(pubid=group.pubid), expect_errors=True
        )

        assert res.status_code == 404

    def test_it_returns_http_200_for_private_group_with_creator_authentication(
        self, app, user_with_token, token_auth_header, factories, db_session
    ):
        user, _ = user_with_token
        group = factories.Group(creator=user, memberships=[GroupMembership(user=user)])
        db_session.commit()

        res = app.get(
            "/api/groups/{pubid}".format(pubid=group.pubid), headers=token_auth_header
        )

        assert res.status_code == 200

    def test_it_returns_http_200_for_private_group_with_member_authentication(
        self, app, user_with_token, token_auth_header, factories, db_session
    ):
        user, _ = user_with_token
        group = factories.Group()
        group.memberships.append(GroupMembership(user=user))
        db_session.commit()

        res = app.get(
            "/api/groups/{pubid}".format(pubid=group.pubid), headers=token_auth_header
        )

        assert res.status_code == 200

    def test_it_returns_http_404_for_private_group_if_token_user_not_creator(
        self, app, token_auth_header, factories, db_session
    ):
        group = factories.Group()
        db_session.commit()

        res = app.get(
            "/api/groups/{pubid}".format(pubid=group.pubid),
            headers=token_auth_header,
            expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_returns_http_200_for_private_group_with_auth_client_matching_authority(
        self, app, auth_client_header, factories, db_session
    ):
        group = factories.Group(authority="thirdparty.com")
        db_session.commit()

        res = app.get(
            "/api/groups/{pubid}".format(pubid=group.pubid), headers=auth_client_header
        )

        assert res.status_code == 200

    def test_it_returns_http_404_for_private_group_with_auth_client_mismatched_authority(
        self, app, auth_client_header, factories, db_session
    ):
        group = factories.Group(authority="somewhere-else.com")
        db_session.commit()

        res = app.get(
            "/api/groups/{pubid}".format(pubid=group.pubid),
            headers=auth_client_header,
            expect_errors=True,
        )

        assert res.status_code == 404


@pytest.fixture
def auth_client(db_session, factories):
    auth_client = factories.ConfidentialAuthClient(
        authority="thirdparty.com", grant_type=GrantType.client_credentials
    )
    db_session.commit()
    return auth_client


@pytest.fixture
def auth_client_header(auth_client):
    user_pass = "{client_id}:{secret}".format(
        client_id=auth_client.id, secret=auth_client.secret
    )
    encoded = base64.standard_b64encode(user_pass.encode("utf-8"))
    return {"Authorization": "Basic {creds}".format(creds=encoded.decode("ascii"))}


@pytest.fixture
def user_with_token(db_session, factories):
    user = factories.User()
    token = factories.DeveloperToken(user=user)
    db_session.add(token)
    db_session.commit()
    return (user, token)


@pytest.fixture
def token_auth_header(user_with_token):
    user, token = user_with_token
    return {"Authorization": "Bearer {}".format(token.value)}
