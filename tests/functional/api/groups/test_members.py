# -*- coding: utf-8 -*-

import pytest


class TestReadMembers:
    def test_it_returns_list_of_members_for_restricted_group_without_authn(
        self, app, factories, db_session
    ):
        group = factories.RestrictedGroup()
        group.members = [factories.User(), factories.User(), factories.User()]
        db_session.commit()

        res = app.get(f"/api/groups/{group.pubid}/members")

        assert res.status_code == 200
        assert len(res.json) == 3

    def test_it_returns_list_of_members_if_user_has_access_to_private_group(
        self, app, factories, db_session, group, user, token_auth_header
    ):
        group.members.append(user)
        db_session.commit()

        res = app.get(f"/api/groups/{group.pubid}/members", headers=token_auth_header,)

        returned_usernames = [member["username"] for member in res.json]
        assert user.username in returned_usernames
        assert group.creator.username in returned_usernames

        assert res.status_code == 200

    def test_it_returns_404_if_user_does_not_have_read_access_to_group(
        self, app, user_3rd_party, db_session, factories, user, token_auth_header
    ):
        group = factories.Group(creator=user_3rd_party)
        db_session.commit()

        # This user is not a member of the group
        res = app.get(
            f"/api/groups/{group.pubid}/members",
            headers=token_auth_header,
            expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_returns_empty_list_if_no_members_in_group(self, app):
        res = app.get("/api/groups/__world__/members")

        assert res.json == []


class TestAddMember:
    def test_it_returns_http_204_when_successful(self, app, user, group, auth_header):
        res = app.post_json(
            f"/api/groups/{group.pubid}/members/{user.userid}", headers=auth_header,
        )

        assert res.status_code == 204

    def test_it_adds_member_to_group(self, app, user, group, auth_header):
        app.post_json(
            f"/api/groups/{group.pubid}/members/{user.userid}", headers=auth_header,
        )

        assert user in group.members

    def test_it_ignores_forwarded_user_header(
        self, app, user, factories, group, db_session, auth_header,
    ):
        headers = auth_header
        user2 = factories.User(authority="thirdparty.example.com")
        db_session.commit()

        headers["X-Forwarded-User"] = user.userid

        res = app.post_json(
            f"/api/groups/{group.pubid}/members/{user.userid}", headers=auth_header,
        )

        assert user in group.members
        assert user2 not in group.members
        assert res.status_code == 204

    def test_it_is_idempotent(self, app, user, group, auth_header):
        app.post_json(
            f"/api/groups/{group.pubid}/members/{user.userid}", headers=auth_header,
        )

        res = app.post_json(
            f"/api/groups/{group.pubid}/members/{user.userid}", headers=auth_header,
        )

        assert user in group.members
        assert res.status_code == 204

    def test_it_returns_404_if_authority_mismatch_on_user(
        self, app, factories, group, auth_header
    ):
        user = factories.User(authority="somewhere-else.org")
        res = app.post_json(
            f"/api/groups/{group.pubid}/members/{user.userid}",
            headers=auth_header,
            expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_returns_404_if_malformed_userid(
        self, app, factories, group, auth_header
    ):
        bad_user_id = "foo@bar.com"
        res = app.post_json(
            f"/api/groups/{group.pubid}/members/{bad_user_id}",
            headers=auth_header,
            expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_returns_404_if_authority_mismatch_on_group(
        self, app, factories, auth_header
    ):
        bad_user = factories.User(authority="bad.example.com")
        group = factories.Group(authority="somewhere-else.org")
        res = app.post_json(
            f"/api/groups/{group.pubid}/members/{bad_user.userid}",
            headers=auth_header,
            expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_returns_404_if_missing_auth(self, app, user, group):
        res = app.post_json(
            f"/api/groups/{group.pubid}/members/{user.userid}", expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_returns_404_with_token_auth(self, app, token_auth_header, user, group):
        res = app.post_json(
            f"/api/groups/{group.pubid}/members/{user.userid}",
            headers=token_auth_header,
            expect_errors=True,
        )

        assert res.status_code == 404


class TestRemoveMember:
    def test_it_removes_authed_user_from_group(
        self, app, group, group_member_with_token
    ):

        group_member, token = group_member_with_token
        headers = {"Authorization": f"Bearer {token.value}"}

        app.delete(f"/api/groups/{group.pubid}/members/me", headers=headers)

        # We currently have no elegant way to check this via the API, but in a
        # future version we should be able to make a GET request here for the
        # group information and check it 404s
        assert group_member not in group.members


@pytest.fixture
def group_member(group, db_session, factories):
    user = factories.User()
    group.members.append(user)
    db_session.commit()
    return user


@pytest.fixture
def group_member_with_token(group_member, db_session, factories):
    token = factories.DeveloperToken(userid=group_member.userid)
    db_session.add(token)
    db_session.commit()
    return (group_member, token)
