import base64

import pytest

from h.models import GroupMembership, Token
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
        self, app, factories, db_session
    ):
        group = factories.Group()
        user = factories.User()
        token = factories.DeveloperToken(user=user)
        group.memberships.extend(
            [GroupMembership(user=user), GroupMembership(user=factories.User())]
        )
        db_session.commit()

        res = app.get(
            "/api/groups/{pubid}/members".format(pubid=group.pubid),
            headers=self.authorization_header(token),
        )

        returned_usernames = [member["username"] for member in res.json]
        assert returned_usernames == [member.username for member in group.members]
        assert res.status_code == 200

    def test_it_returns_404_if_user_does_not_have_read_access_to_group(
        self, app, db_session, factories
    ):
        group = factories.Group()
        db_session.commit()

        res = app.get(
            "/api/groups/{pubid}/members".format(pubid=group.pubid),
            headers=self.authorization_header(factories.DeveloperToken()),
            expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_returns_empty_list_if_no_members_in_group(self, app):
        res = app.get("/api/groups/__world__/members")

        assert res.json == []

    @staticmethod
    def authorization_header(token) -> dict:
        """Return an Authorization header for the given developer token."""
        return {"Authorization": "Bearer {}".format(token.value)}


class TestAddMember:
    def test_it_returns_http_204_when_successful(
        self, app, auth_client, db_session, factories
    ):
        third_party_user = factories.User(authority="thirdparty.com")
        third_party_group = factories.Group(authority="thirdparty.com")
        db_session.commit()

        res = app.post_json(
            "/api/groups/{pubid}/members/{userid}".format(
                pubid=third_party_group.pubid, userid=third_party_user.userid
            ),
            headers=self.authorization_header(auth_client),
        )

        assert res.status_code == 204

    def test_it_adds_member_to_group(self, app, auth_client, db_session, factories):
        third_party_user = factories.User(authority="thirdparty.com")
        third_party_group = factories.Group(authority="thirdparty.com")
        db_session.commit()

        app.post_json(
            "/api/groups/{pubid}/members/{userid}".format(
                pubid=third_party_group.pubid, userid=third_party_user.userid
            ),
            headers=self.authorization_header(auth_client),
        )

        assert third_party_user in third_party_group.members

    def test_it_ignores_forwarded_user_header(
        self, app, factories, db_session, auth_client
    ):
        third_party_user = factories.User(authority="thirdparty.com")
        third_party_group = factories.Group(authority="thirdparty.com")
        headers = self.authorization_header(auth_client)
        user2 = factories.User(authority="thirdparty.com")
        db_session.commit()

        headers["X-Forwarded-User"] = third_party_user.userid

        res = app.post_json(
            "/api/groups/{pubid}/members/{userid}".format(
                pubid=third_party_group.pubid, userid=third_party_user.userid
            ),
            headers=headers,
        )

        assert third_party_user in third_party_group.members
        assert user2 not in third_party_group.members
        assert res.status_code == 204

    def test_it_is_idempotent(self, app, auth_client, db_session, factories):
        third_party_user = factories.User(authority="thirdparty.com")
        third_party_group = factories.Group(authority="thirdparty.com")
        db_session.commit()

        app.post_json(
            "/api/groups/{pubid}/members/{userid}".format(
                pubid=third_party_group.pubid, userid=third_party_user.userid
            ),
            headers=self.authorization_header(auth_client),
        )

        res = app.post_json(
            "/api/groups/{pubid}/members/{userid}".format(
                pubid=third_party_group.pubid, userid=third_party_user.userid
            ),
            headers=self.authorization_header(auth_client),
        )

        assert third_party_user in third_party_group.members
        assert res.status_code == 204

    def test_it_returns_404_if_authority_mismatch_on_user(
        self, app, factories, auth_client
    ):
        group = factories.Group()
        user = factories.User(authority="somewhere-else.org")

        res = app.post_json(
            "/api/groups/{pubid}/members/{userid}".format(
                pubid=group.pubid, userid=user.userid
            ),
            headers=self.authorization_header(auth_client),
            expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_returns_404_if_malformed_userid(
        self, app, factories, auth_client, db_session
    ):
        group = factories.Group()
        db_session.commit()

        res = app.post_json(
            "/api/groups/{pubid}/members/{userid}".format(
                pubid=group.pubid, userid="foo@bar.com"
            ),
            headers=self.authorization_header(auth_client),
            expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_returns_404_if_authority_mismatch_on_group(
        self, app, factories, user, auth_client, db_session
    ):
        group = factories.Group(authority="somewhere-else.org")
        db_session.commit()

        res = app.post_json(
            "/api/groups/{pubid}/members/{userid}".format(
                pubid=group.pubid, userid=user.userid
            ),
            headers=self.authorization_header(auth_client),
            expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_returns_404_if_missing_auth(self, app, user, db_session, factories):
        group = factories.Group()
        db_session.commit()

        res = app.post_json(
            "/api/groups/{pubid}/members/{userid}".format(
                pubid=group.pubid, userid=user.userid
            ),
            expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_returns_404_with_token_auth(
        self, app, token_auth_header, user, db_session, factories
    ):
        group = factories.Group()
        db_session.commit()

        res = app.post_json(
            "/api/groups/{pubid}/members/{userid}".format(
                pubid=group.pubid, userid=user.userid
            ),
            headers=token_auth_header,
            expect_errors=True,
        )

        assert res.status_code == 404

    @pytest.fixture
    def auth_client(self, factories):
        return factories.ConfidentialAuthClient(
            authority="thirdparty.com", grant_type=GrantType.client_credentials
        )

    @staticmethod
    def authorization_header(auth_client) -> dict:
        """Return an Authorization header for the given AuthClient."""
        user_pass = "{client_id}:{secret}".format(
            client_id=auth_client.id, secret=auth_client.secret
        )
        encoded = base64.standard_b64encode(user_pass.encode("utf-8"))
        return {"Authorization": "Basic {creds}".format(creds=encoded.decode("ascii"))}


class TestRemoveMember:
    def test_it_removes_authed_user_from_group(self, app, db_session, factories):
        group = factories.Group()
        group_member = factories.User()
        group.memberships.append(GroupMembership(user=group_member))
        token = factories.DeveloperToken(user=group_member)
        db_session.add(token)
        headers = {"Authorization": "Bearer {}".format(token.value)}
        db_session.commit()

        app.delete("/api/groups/{}/members/me".format(group.pubid), headers=headers)

        # We currently have no elegant way to check this via the API, but in a
        # future version we should be able to make a GET request here for the
        # group information and check it 404s
        assert group_member not in group.members
