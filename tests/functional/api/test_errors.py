# -*- coding: utf-8 -*-
"""
Functional tests for client API errors

Uses create-group endpoint as it can raise all relevant client error codes.
"""

from __future__ import unicode_literals

import pytest
import base64
import re


from h.models.auth_client import GrantType

native_str = str


@pytest.mark.functional
class Test400Errors(object):
    """Creating a group can raise all of the client errors we want to test"""

    def test_it_400s_if_invalid_payload(self, app, append_token_auth):
        group = {}
        headers = append_token_auth()
        res = app.post_json("/api/groups", group, headers=headers, expect_errors=True)

        assert res.status_code == 400
        stripped = _strip_unicode_literal(res.json["reason"])
        assert stripped == "'name' is a required property"

    def test_it_400s_for_create_group_if_groupid_set_on_default_authority(
        self, app, append_token_auth
    ):
        group = {"name": "My Group", "groupid": "3434kjkjk"}
        headers = append_token_auth()
        res = app.post_json("/api/groups", group, headers=headers, expect_errors=True)
        stripped = _strip_unicode_literal(res.json["reason"])
        # FIXME: The `reason` is double-escaped
        expected = "groupid: '3434kjkjk' does not match \"^group:([a-zA-Z0-9._\\\\-+!~*()']{1,1024})@(.*)$\""

        assert res.status_code == 400
        assert stripped == expected


@pytest.mark.functional
class Test404Errors(object):
    # TODO: Some of these 404s should really be 403s
    def test_it_404s_if_authz_fail_with_valid_accept(self, app, append_auth_client):
        headers = append_auth_client()
        headers[native_str("Accept")] = native_str("application/json")
        group = {"name": "My Group"}

        res = app.post_json("/api/groups", group, headers=headers, expect_errors=True)

        assert res.status_code == 404
        assert (
            res.json["reason"]
            == "Either the resource you requested doesn't exist, or you are not currently authorized to see it."
        )

    def test_it_404s_if_authz_fail_with_missing_accept(self, app, append_auth_client):
        headers = append_auth_client()
        group = {"name": "My Group"}

        res = app.post_json("/api/groups", group, headers=headers, expect_errors=True)

        assert res.status_code == 404
        assert (
            res.json["reason"]
            == "Either the resource you requested doesn't exist, or you are not currently authorized to see it."
        )

    def test_it_404s_if_not_found_with_valid_accept_and_no_authz(self, app):
        headers = {}
        headers[native_str("Accept")] = native_str("application/json")

        res = app.get("/api/not_a_thing", headers=headers, expect_errors=True)

        assert res.status_code == 404
        assert (
            res.json["reason"]
            == "Either the resource you requested doesn't exist, or you are not currently authorized to see it."
        )

    def test_it_404s_if_not_found_with_missing_accept_and_no_authz(self, app):
        res = app.get("/api/not_a_thing", expect_errors=True)

        assert res.status_code == 404
        assert (
            res.json["reason"]
            == "Either the resource you requested doesn't exist, or you are not currently authorized to see it."
        )


@pytest.mark.functional
class Test409Errors(object):
    def test_it_409s_on_create_group_if_groupid_is_duplicate(
        self, app, append_auth_client, third_party_user
    ):
        headers = append_auth_client()
        headers[native_str("X-Forwarded-User")] = native_str(third_party_user.userid)
        group = {"name": "My Group", "groupid": "group:333vcdfkj~@thirdparty.com"}

        res = app.post_json("/api/groups", group, headers=headers)
        res = app.post_json("/api/groups", group, headers=headers, expect_errors=True)

        assert res.status_code == 409
        assert (
            res.json["reason"]
            == "group with groupid 'group:333vcdfkj~@thirdparty.com' already exists"
        )


@pytest.mark.functional
class Test415Errors(object):
    def test_it_415s_if_not_found_with_bad_accept(self, app):
        headers = {}
        headers[native_str("Accept")] = native_str("application/totally_random")
        res = app.get("/api/not_a_thing", headers=headers, expect_errors=True)

        assert res.status_code == 415
        assert res.json["reason"] == "Unsupported media type"

    def test_it_415s_if_path_extant_but_bad_accept(self, app):
        headers = {}
        headers[native_str("Accept")] = native_str("application/totally_random")
        res = app.get("/api/groups", headers=headers, expect_errors=True)

        assert res.status_code == 415
        assert res.json["reason"] == "Unsupported media type"


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
    user_pass = "{client_id}:{secret}".format(
        client_id=auth_client.id, secret=auth_client.secret
    )
    encoded = base64.standard_b64encode(user_pass.encode("utf-8"))

    def append_header(headers=None):
        headers = headers or {}
        headers[native_str("Authorization")] = native_str(
            "Basic {creds}".format(creds=encoded.decode("ascii"))
        )
        return headers

    return append_header


@pytest.fixture
def user_with_token(db_session, factories):
    user = factories.User()
    token = factories.DeveloperToken(userid=user.userid)
    db_session.commit()
    return (user, token)


@pytest.fixture
def append_token_auth(user_with_token):
    def append_header(headers=None):
        headers = headers or {}
        user, token = user_with_token
        headers[native_str("Authorization")] = native_str(
            "Bearer {}".format(token.value)
        )
        return headers

    return append_header


@pytest.fixture
def valid_accept():
    headers = {}
    headers[native_str("Accept")] = "application/json"
    return headers


def _strip_unicode_literal(original):
    # Strip "u" literal prefixes that get added in front of property names in
    # certain error messages in Python 2.
    # See https://github.com/hypothesis/h/commit/992fa8005389ed52ebd076ae230d862b24449f2f
    return re.sub(r"u(['\"])([^']+)'", "\\1\\2'", original)
