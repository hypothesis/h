# -*- coding: utf-8 -*-
"""
Functional tests for client API errors

Uses create-group endpoint as it can raise all relevant client error codes.
"""

from __future__ import unicode_literals

import pytest
import base64


from h.models.auth_client import GrantType

native_str = str


@pytest.mark.functional
class Test400ErrorsUsingCreateGroup(object):
    """Creating a group can raise all of the client errors we want to test"""

    def test_it_returns_http_400_with_invalid_payload(self, app, token_auth_header):
        group = {}

        res = app.post_json(
            "/api/groups", group, headers=token_auth_header, expect_errors=True
        )

        assert res.status_code == 400

    def test_it_returns_a_formatted_reason_with_invalid_payload(
        self, app, token_auth_header
    ):
        group = {}

        res = app.post_json(
            "/api/groups", group, headers=token_auth_header, expect_errors=True
        )

        assert res.json["reason"] == "u'name' is a required property"

    def test_it_returns_http_400_if_groupid_set_on_default_authority(
        self, app, token_auth_header
    ):
        group = {"name": "My Group", "groupid": "3434kjkjk"}
        res = app.post_json(
            "/api/groups", group, headers=token_auth_header, expect_errors=True
        )

        assert res.status_code == 400

    def test_it_returns_formatted_reason_if_groupid_set_on_default_authority(
        self, app, token_auth_header
    ):
        # FIXME: The `reason` is double-escaped
        group = {"name": "My Group", "groupid": "3434kjkjk"}
        res = app.post_json(
            "/api/groups", group, headers=token_auth_header, expect_errors=True
        )

        assert (
            res.json["reason"]
            == "groupid: u'3434kjkjk' does not match u\"^group:([a-zA-Z0-9._\\\\-+!~*()']{1,1024})@(.*)$\""
        )


@pytest.mark.functional
class Test403ErrorsUsingCreateGroup(object):
    # FIXME: API currently converts all 403s to 404s
    def test_it_returns_http_404_if_no_authenticated_user(
        self, app, auth_client_header
    ):
        # FIXME: This should return a 403
        group = {"name": "My Group"}
        res = app.post_json(
            "/api/groups", group, headers=auth_client_header, expect_errors=True
        )

        assert res.status_code == 404

    def test_it_returns_formatted_reason_if_no_authenticated_user(
        self, app, auth_client_header
    ):
        # FIXME: This should return a 403
        group = {"name": "My Group"}
        res = app.post_json(
            "/api/groups", group, headers=auth_client_header, expect_errors=True
        )

        assert (
            res.json["reason"]
            == "Either the resource you requested doesn't exist, or you are not currently authorized to see it."
        )

    @pytest.mark.xfail
    def test_it_returns_http_403_if_no_authenticated_user(
        self, app, auth_client_header
    ):
        group = {"name": "My Group"}
        res = app.post_json(
            "/api/groups", group, headers=auth_client_header, expect_errors=True
        )

        assert res.status_code == 403


@pytest.mark.functional
class Test404ErrorsUsingCreateGroup(object):
    def test_it_returns_http_404_if_endpoint_nonexistent(self, app):
        res = app.get("/api/not_a_thing", expect_errors=True)

        assert res.status_code == 404

    def test_it_returns_formatted_reason_if_endpoint_nonexistent(self, app):
        res = app.get("/api/not_a_thing", expect_errors=True)

        assert (
            res.json["reason"]
            == "Either the resource you requested doesn't exist, or you are not currently authorized to see it."
        )


@pytest.mark.functional
class Test409ErrorsUsingCreateGroup(object):
    def test_it_returns_HTTP_Conflict_if_groupid_is_duplicate(
        self, app, auth_client_header, third_party_user
    ):
        headers = auth_client_header
        headers[native_str("X-Forwarded-User")] = native_str(third_party_user.userid)
        group = {"name": "My Group", "groupid": "group:333vcdfkj~@thirdparty.com"}

        res = app.post_json("/api/groups", group, headers=headers)
        res = app.post_json("/api/groups", group, headers=headers, expect_errors=True)

        assert res.status_code == 409

    def test_it_returns_formatted_reason_if_group_is_duplicate(
        self, app, auth_client_header, third_party_user
    ):
        headers = auth_client_header
        headers[native_str("X-Forwarded-User")] = native_str(third_party_user.userid)
        group = {"name": "My Group", "groupid": "group:333vcdfkj~@thirdparty.com"}

        res = app.post_json("/api/groups", group, headers=headers)
        res = app.post_json("/api/groups", group, headers=headers, expect_errors=True)

        assert (
            res.json["reason"]
            == "group with groupid 'group:333vcdfkj~@thirdparty.com' already exists"
        )


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
    return {
        native_str("Authorization"): native_str(
            "Basic {creds}".format(creds=encoded.decode("ascii"))
        )
    }


@pytest.fixture
def user_with_token(db_session, factories):
    user = factories.User()
    token = factories.DeveloperToken(userid=user.userid)
    db_session.add(token)
    db_session.commit()
    return (user, token)


@pytest.fixture
def token_auth_header(user_with_token):
    user, token = user_with_token
    return {native_str("Authorization"): native_str("Bearer {}".format(token.value))}
