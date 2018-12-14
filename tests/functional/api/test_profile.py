# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

# String type for request/response headers and metadata in WSGI.
#
# Per PEP-3333, this is intentionally `str` under both Python 2 and 3, even
# though it has different meanings.
#
# See https://www.python.org/dev/peps/pep-3333/#a-note-on-string-types
native_str = str


@pytest.mark.functional
class TestGetProfile(object):
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

        headers = {"Authorization": str("Bearer {}".format(token.value))}

        res = app.get("/api/profile", headers=headers)

        assert res.json["userid"] == user.userid
        assert [group["id"] for group in res.json["groups"]] == ["__world__"]

    def test_it_returns_profile_for_third_party_authd_user(
        self, app, open_group, third_party_user_with_token
    ):
        """Fetch a profile for a third-party account."""

        user, token = third_party_user_with_token

        headers = {"Authorization": str("Bearer {}".format(token.value))}

        res = app.get("/api/profile", headers=headers)

        assert res.json["userid"] == user.userid

        group_ids = [group["id"] for group in res.json["groups"]]
        # The profile API returns no open groups for third-party accounts.
        # (The client gets open groups from the groups API instead.)
        assert group_ids == []


@pytest.mark.functional
class TestPatchProfile(object):
    def test_it_allows_authenticated_user(self, app, user_with_token):
        """PATCH profile will always act on the auth'd user's profile."""

        user, token = user_with_token

        headers = {"Authorization": native_str("Bearer {}".format(token.value))}
        profile = {"preferences": {"show_sidebar_tutorial": True}}

        res = app.patch_json("/api/profile", profile, headers=headers)

        # The ``show_sidebar_tutorial`` property is only present if
        # its value is True
        assert "show_sidebar_tutorial" in res.json["preferences"]
        assert res.status_code == 200

    def test_it_updates_user_profile(self, app, user_with_token):
        """PATCH profile will always act on the auth'd user's profile."""

        user, token = user_with_token

        headers = {"Authorization": native_str("Bearer {}".format(token.value))}
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


@pytest.fixture
def user(db_session, factories):
    user = factories.User()
    db_session.commit()
    return user


@pytest.fixture
def user_with_token(user, db_session, factories):
    token = factories.DeveloperToken(userid=user.userid)
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
    token = factories.DeveloperToken(userid=third_party_user.userid)
    db_session.commit()
    return (third_party_user, token)
