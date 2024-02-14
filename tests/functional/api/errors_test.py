"""
Functional tests for client API errors.

Uses create-group endpoint as it can raise all relevant client error codes.
"""

import base64

import pytest

from h.models.auth_client import GrantType


class Test400Errors:
    # Creating a group can raise all of the client errors we want to test.

    def test_it_400s_if_invalid_payload(self, app, append_token_auth):
        group = {}
        headers = append_token_auth()
        res = app.post_json("/api/groups", group, headers=headers, expect_errors=True)

        assert res.status_code == 400
        assert res.json["reason"] == "'name' is a required property"

    def test_it_400s_for_create_group_if_groupid_set_on_default_authority(
        self, app, append_token_auth
    ):
        group = {"name": "My Group", "groupid": "3434kjkjk"}
        headers = append_token_auth()
        res = app.post_json("/api/groups", group, headers=headers, expect_errors=True)
        reason = res.json["reason"]
        # FIXME: The `reason` is double-escaped
        expected = (
            "groupid: '3434kjkjk'"
            ' does not match "^group:([a-zA-Z0-9._\\\\-+!~*()\']{1,1024})@(.*)$"'
        )

        assert res.status_code == 400
        assert reason == expected


class Test404Errors:
    # TODO: Some of these 404s should really be 403s
    reason_message = (
        "Either the resource you requested doesn't exist,"
        " or you are not currently authorized to see it."
    )

    def test_it_404s_if_authz_fail_with_valid_accept(self, app, append_auth_client):
        headers = append_auth_client()
        headers["Accept"] = "application/json"
        group = {"name": "My Group"}

        res = app.post_json("/api/groups", group, headers=headers, expect_errors=True)

        assert res.status_code == 404
        assert res.json["reason"] == self.reason_message

    def test_it_404s_if_authz_fail_with_missing_accept(self, app, append_auth_client):
        headers = append_auth_client()
        group = {"name": "My Group"}

        res = app.post_json("/api/groups", group, headers=headers, expect_errors=True)

        assert res.status_code == 404
        assert res.json["reason"] == self.reason_message

    def test_it_404s_if_not_found_with_valid_accept_and_no_authz(self, app):
        headers = {}
        headers["Accept"] = "application/json"

        res = app.get("/api/not_a_thing", headers=headers, expect_errors=True)

        assert res.status_code == 404
        assert res.json["reason"] == (
            "Either the resource you requested doesn't exist, "
            "or you are not currently authorized to see it."
        )

    def test_it_404s_if_not_found_with_missing_accept_and_no_authz(self, app):
        res = app.get("/api/not_a_thing", expect_errors=True)

        assert res.status_code == 404
        assert res.json["reason"] == self.reason_message


class Test409Errors:
    def test_it_409s_on_create_group_if_groupid_is_duplicate(
        self, app, append_auth_client, third_party_user
    ):
        headers = append_auth_client()
        headers["X-Forwarded-User"] = third_party_user.userid
        group = {"name": "My Group", "groupid": "group:333vcdfkj~@thirdparty.com"}

        res = app.post_json("/api/groups", group, headers=headers)
        res = app.post_json("/api/groups", group, headers=headers, expect_errors=True)

        assert res.status_code == 409
        assert (
            res.json["reason"]
            == "group with groupid 'group:333vcdfkj~@thirdparty.com' already exists"
        )


class Test406Errors:
    def test_it_406s_if_not_found_with_bad_accept(self, app):
        headers = {}
        headers["Accept"] = "application/totally_random"
        res = app.get("/api/not_a_thing", headers=headers, expect_errors=True)

        assert res.status_code == 406
        assert res.json["reason"] == "Not acceptable"

    def test_it_406s_if_path_extant_but_bad_accept(self, app):
        headers = {}
        headers["Accept"] = "application/totally_random"
        res = app.get("/api/groups", headers=headers, expect_errors=True)

        assert res.status_code == 406
        assert res.json["reason"] == "Not acceptable"


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
def append_auth_client(auth_client):
    user_pass = f"{auth_client.id}:{auth_client.secret}"
    encoded = base64.standard_b64encode(user_pass.encode("utf-8"))

    def append_header(headers=None):
        headers = headers or {}
        headers["Authorization"] = f"Basic {encoded.decode('ascii')}"
        return headers

    return append_header


@pytest.fixture
def user_with_token(db_session, factories):
    user = factories.User()
    token = factories.DeveloperToken(user=user)
    db_session.commit()
    return (user, token)


@pytest.fixture
def append_token_auth(user_with_token):
    def append_header(headers=None):
        headers = headers or {}
        _, token = user_with_token
        headers["Authorization"] = f"Bearer {token.value}"
        return headers

    return append_header


@pytest.fixture
def valid_accept():
    headers = {}
    headers["Accept"] = "application/json"
    return headers
