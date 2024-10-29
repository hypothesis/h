import base64

import pytest

from h.models import GroupMembership
from h.models.auth_client import GrantType


class TestReadMembers:
    def test_it_returns_list_of_members_for_restricted_group_without_authn(
        self, app, factories, db_session
    ):
        group = factories.RestrictedGroup(
            memberships=[
                GroupMembership(user=user)
                for user in factories.User.create_batch(size=3)
            ]
        )
        db_session.commit()

        res = app.get("/api/groups/{pubid}/members".format(pubid=group.pubid))

        assert res.status_code == 200
        assert len(res.json) == 3

    def test_it_returns_list_of_members_if_user_has_access_to_private_group(
        self, app, factories, db_session, group, user_with_token, token_auth_header
    ):
        user, _ = user_with_token
        group.memberships.extend(
            [GroupMembership(user=user), GroupMembership(user=factories.User())]
        )
        db_session.commit()

        res = app.get(
            "/api/groups/{pubid}/members".format(pubid=group.pubid),
            headers=token_auth_header,
        )

        returned_usernames = [member["username"] for member in res.json]
        assert returned_usernames == [member.username for member in group.members]
        assert res.status_code == 200

    def test_it_returns_404_if_user_does_not_have_read_access_to_group(
        self, app, group, user_with_token, token_auth_header
    ):
        # This user is not a member of the group
        user, _ = user_with_token
        res = app.get(
            "/api/groups/{pubid}/members".format(pubid=group.pubid),
            headers=token_auth_header,
            expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_returns_empty_list_if_no_members_in_group(self, app):
        res = app.get("/api/groups/__world__/members")

        assert res.json == []


class TestAddMember:
    def test_it_returns_http_204_when_successful(
        self, app, third_party_user, third_party_group, auth_client_header
    ):
        res = app.post_json(
            "/api/groups/{pubid}/members/{userid}".format(
                pubid=third_party_group.pubid, userid=third_party_user.userid
            ),
            headers=auth_client_header,
        )

        assert res.status_code == 204

    def test_it_adds_member_to_group(
        self, app, third_party_user, third_party_group, auth_client_header
    ):
        app.post_json(
            "/api/groups/{pubid}/members/{userid}".format(
                pubid=third_party_group.pubid, userid=third_party_user.userid
            ),
            headers=auth_client_header,
        )

        assert third_party_user in third_party_group.members

    def test_it_ignores_forwarded_user_header(
        self,
        app,
        third_party_user,
        factories,
        third_party_group,
        db_session,
        auth_client_header,
    ):
        headers = auth_client_header
        user2 = factories.User(authority="thirdparty.com")
        db_session.commit()

        headers["X-Forwarded-User"] = third_party_user.userid

        res = app.post_json(
            "/api/groups/{pubid}/members/{userid}".format(
                pubid=third_party_group.pubid, userid=third_party_user.userid
            ),
            headers=auth_client_header,
        )

        assert third_party_user in third_party_group.members
        assert user2 not in third_party_group.members
        assert res.status_code == 204

    def test_it_is_idempotent(
        self, app, third_party_user, third_party_group, auth_client_header
    ):
        app.post_json(
            "/api/groups/{pubid}/members/{userid}".format(
                pubid=third_party_group.pubid, userid=third_party_user.userid
            ),
            headers=auth_client_header,
        )

        res = app.post_json(
            "/api/groups/{pubid}/members/{userid}".format(
                pubid=third_party_group.pubid, userid=third_party_user.userid
            ),
            headers=auth_client_header,
        )

        assert third_party_user in third_party_group.members
        assert res.status_code == 204

    def test_it_returns_404_if_authority_mismatch_on_user(
        self, app, factories, group, auth_client_header
    ):
        user = factories.User(authority="somewhere-else.org")
        res = app.post_json(
            "/api/groups/{pubid}/members/{userid}".format(
                pubid=group.pubid, userid=user.userid
            ),
            headers=auth_client_header,
            expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_returns_404_if_malformed_userid(
        self, app, factories, group, auth_client_header
    ):
        res = app.post_json(
            "/api/groups/{pubid}/members/{userid}".format(
                pubid=group.pubid, userid="foo@bar.com"
            ),
            headers=auth_client_header,
            expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_returns_404_if_authority_mismatch_on_group(
        self, app, factories, user, auth_client_header
    ):
        group = factories.Group(authority="somewhere-else.org")
        res = app.post_json(
            "/api/groups/{pubid}/members/{userid}".format(
                pubid=group.pubid, userid=user.userid
            ),
            headers=auth_client_header,
            expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_returns_404_if_missing_auth(self, app, user, group):
        res = app.post_json(
            "/api/groups/{pubid}/members/{userid}".format(
                pubid=group.pubid, userid=user.userid
            ),
            expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_returns_404_with_token_auth(self, app, token_auth_header, user, group):
        res = app.post_json(
            "/api/groups/{pubid}/members/{userid}".format(
                pubid=group.pubid, userid=user.userid
            ),
            headers=token_auth_header,
            expect_errors=True,
        )

        assert res.status_code == 404


class TestRemoveMember:
    def test_it_removes_authed_user_from_group(
        self, app, group, group_member_with_token
    ):
        group_member, token = group_member_with_token
        headers = {"Authorization": "Bearer {}".format(token.value)}

        app.delete("/api/groups/{}/members/me".format(group.pubid), headers=headers)

        # We currently have no elegant way to check this via the API, but in a
        # future version we should be able to make a GET request here for the
        # group information and check it 404s
        assert group_member not in group.members


@pytest.fixture
def user(db_session, factories):
    user = factories.User(authority="example.com")
    db_session.commit()
    return user


@pytest.fixture
def third_party_user(db_session, factories):
    user = factories.User(authority="thirdparty.com")
    db_session.commit()
    return user


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
def group(db_session, factories):
    group = factories.Group()
    db_session.commit()
    return group


@pytest.fixture
def third_party_group(db_session, factories):
    group = factories.Group(authority="thirdparty.com")
    db_session.commit()
    return group


@pytest.fixture
def group_member(group, db_session, factories):
    user = factories.User()
    group.memberships.append(GroupMembership(user=user))
    db_session.commit()
    return user


@pytest.fixture
def group_member_with_token(group_member, db_session, factories):
    token = factories.DeveloperToken(user=group_member)
    db_session.add(token)
    db_session.commit()
    return (group_member, token)


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
