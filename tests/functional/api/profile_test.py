import pytest

from h.models import GroupMembership


class TestGetProfile:
    def test_it_returns_profile_with_single_group_when_not_authd(self, app):
        """
        Fetch an anonymous "profile".

        With no authentication and no authority parameter, this should default
        to the site's `authority` and show only the global group.
        """
        res = app.get("/api/profile")

        assert res.json["userid"] is None
        assert res.json["authority"] == "example.com"
        assert [group["id"] for group in res.json["groups"]] == ["__world__"]

    def test_it_returns_profile_for_authenticated_user(self, app, user_with_token):
        """Fetch a profile through the API for an authenticated user."""

        user, token = user_with_token

        headers = {"Authorization": f"Bearer {token.value}"}

        res = app.get("/api/profile", headers=headers)

        assert res.json["userid"] == user.userid

    def test_it_returns_profile_for_third_party_authd_user(
        self, app, third_party_user_with_token
    ):
        """Fetch a profile for a third-party account."""

        user, token = third_party_user_with_token

        headers = {"Authorization": f"Bearer {token.value}"}

        res = app.get("/api/profile", headers=headers)

        assert res.json["userid"] == user.userid

        group_ids = [group["id"] for group in res.json["groups"]]
        # The profile API returns no open groups for third-party accounts.
        # (The client gets open groups from the groups API instead.)
        assert group_ids == []


class TestGetProfileGroups:
    def test_it_returns_empty_list_when_not_authed(self, app):
        res = app.get("/api/profile/groups")

        assert res.json == []

    def test_it_returns_users_groups_when_authed(self, app, user_with_token, groups):
        _, token = user_with_token
        user_groupids = [group.pubid for group in groups].sort()

        headers = {"Authorization": f"Bearer {token.value}"}

        res = app.get("/api/profile/groups", headers=headers)

        returned_groupids = [group["id"] for group in res.json].sort()

        assert user_groupids == returned_groupids

    def test_it_returns_group_properties(self, app, user_with_token):
        _, token = user_with_token

        headers = {"Authorization": f"Bearer {token.value}"}

        res = app.get("/api/profile/groups", headers=headers)

        for key in ["id", "name", "scoped", "type"]:
            assert key in res.json[0]


class TestPatchProfile:
    def test_it_allows_authenticated_user(self, app, user_with_token):
        """PATCH profile will always act on the auth'd user's profile."""

        _, token = user_with_token

        headers = {"Authorization": f"Bearer {token.value}"}
        profile = {"preferences": {"show_sidebar_tutorial": True}}

        res = app.patch_json("/api/profile", profile, headers=headers)

        # The ``show_sidebar_tutorial`` property is only present if
        # its value is True
        assert "show_sidebar_tutorial" in res.json["preferences"]
        assert res.status_code == 200

    def test_it_updates_user_profile(self, app, user_with_token):
        """PATCH profile will always act on the auth'd user's profile."""

        _, token = user_with_token

        headers = {"Authorization": f"Bearer {token.value}"}
        profile = {"preferences": {"show_sidebar_tutorial": False}}

        res = app.patch_json("/api/profile", profile, headers=headers)

        # The ``show_sidebar_tutorial`` property is only present if
        # its value is True
        assert "show_sidebar_tutorial" not in res.json["preferences"]
        assert res.status_code == 200

    def test_it_raises_http_404_if_unauthenticated(self, app):
        # FIXME: This should return a 403
        profile = {"preferences": {"show_sidebar_tutorial": False}}

        res = app.patch_json("/api/profile", profile, expect_errors=True)

        assert res.status_code == 404

    @pytest.mark.xfail
    def test_it_raises_http_403_if_unauthenticated(self, app):
        profile = {"preferences": {"show_sidebar_tutorial": False}}

        res = app.patch_json("/api/profile", profile, expect_errors=True)

        assert res.status_code == 403

    def test_it_raises_http_400_for_disallowed_setting(self, app, user_with_token):
        _, token = user_with_token
        profile = {"preferences": {"foo": "bar"}}
        headers = {"Authorization": f"Bearer {token.value}"}

        res = app.patch_json(
            "/api/profile", profile, headers=headers, expect_errors=True
        )

        assert res.status_code == 400
        assert res.json["reason"] == "settings with keys foo are not allowed"


@pytest.fixture
def groups(factories):
    groups = [
        factories.Group(),
        factories.Group(),
        factories.RestrictedGroup(),
        factories.OpenGroup(),
    ]
    return groups


@pytest.fixture
def user(groups, db_session, factories):
    user = factories.User(
        memberships=[GroupMembership(group=group) for group in groups]
    )
    db_session.commit()
    return user


@pytest.fixture
def user_with_token(user, db_session, factories):
    token = factories.DeveloperToken(user=user)
    db_session.add(token)
    db_session.commit()
    return (user, token)


@pytest.fixture
def auth_client(db_session, factories):
    auth_client = factories.AuthClient(authority="thirdparty.example.org")
    db_session.commit()
    return auth_client


@pytest.fixture
def third_party_user(auth_client, db_session, factories):
    user = factories.User(authority=auth_client.authority)
    db_session.commit()
    return user


@pytest.fixture
def open_group(auth_client, db_session, factories):
    group = factories.OpenGroup(authority=auth_client.authority)
    db_session.commit()
    return group


@pytest.fixture
def third_party_user_with_token(third_party_user, db_session, factories):
    token = factories.DeveloperToken(user=third_party_user)
    db_session.commit()
    return (third_party_user, token)
