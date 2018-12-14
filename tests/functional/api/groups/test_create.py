# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import base64


from h.models.auth_client import GrantType

native_str = str


@pytest.mark.functional
class TestCreateGroup(object):
    def test_it_returns_http_200_with_valid_payload(self, app, token_auth_header):
        group = {"name": "My Group"}
        res = app.post_json("/api/groups", group, headers=token_auth_header)

        assert res.status_code == 200

    def test_it_ignores_non_whitelisted_fields_in_payload(self, app, token_auth_header):
        group = {"name": "My Group", "organization": "foobar", "joinable_by": "whoever"}
        res = app.post_json("/api/groups", group, headers=token_auth_header)

        assert res.status_code == 200

    def test_it_returns_http_400_with_invalid_payload(self, app, token_auth_header):
        group = {}

        res = app.post_json(
            "/api/groups", group, headers=token_auth_header, expect_errors=True
        )

        assert res.status_code == 400

    def test_it_returns_http_400_if_groupid_set_on_default_authority(
        self, app, token_auth_header
    ):
        group = {"name": "My Group", "groupid": "3434kjkjk"}
        res = app.post_json(
            "/api/groups", group, headers=token_auth_header, expect_errors=True
        )

        assert res.status_code == 400

    def test_it_returns_http_404_if_no_authenticated_user(
        self, app, auth_client_header
    ):
        # FIXME: This should return a 403
        group = {"name": "My Group"}
        res = app.post_json(
            "/api/groups", group, headers=auth_client_header, expect_errors=True
        )

        assert res.status_code == 404

    @pytest.mark.xfail
    def test_it_returns_http_403_if_no_authenticated_user(
        self, app, auth_client_header
    ):
        group = {"name": "My Group"}
        res = app.post_json(
            "/api/groups", group, headers=auth_client_header, expect_errors=True
        )

        assert res.status_code == 403

    def test_it_allows_auth_client_with_forwarded_user(
        self, app, auth_client_header, third_party_user
    ):
        headers = auth_client_header
        headers[native_str("X-Forwarded-User")] = native_str(third_party_user.userid)
        group = {"name": "My Group"}

        res = app.post_json("/api/groups", group, headers=headers)

        assert res.status_code == 200

    def test_it_allows_groupdid_from_auth_client_with_forwarded_user(
        self, app, auth_client_header, third_party_user
    ):
        headers = auth_client_header
        headers[native_str("X-Forwarded-User")] = native_str(third_party_user.userid)
        group = {"name": "My Group", "groupid": "group:333vcdfkj~@thirdparty.com"}

        res = app.post_json("/api/groups", group, headers=headers)
        data = res.json

        assert res.status_code == 200
        assert "groupid" in data
        assert data["groupid"] == "group:{groupid}@thirdparty.com".format(
            groupid="333vcdfkj~"
        )

    def test_it_returns_HTTP_Conflict_if_groupid_is_duplicate(
        self, app, auth_client_header, third_party_user
    ):
        headers = auth_client_header
        headers[native_str("X-Forwarded-User")] = native_str(third_party_user.userid)
        group = {"name": "My Group", "groupid": "group:333vcdfkj~@thirdparty.com"}

        res = app.post_json("/api/groups", group, headers=headers)
        res = app.post_json("/api/groups", group, headers=headers, expect_errors=True)

        assert res.status_code == 409

    def test_it_returns_http_404_with_invalid_forwarded_user_format(
        self, app, auth_client_header
    ):
        # FIXME: This should return a 403
        headers = auth_client_header
        headers[native_str("X-Forwarded-User")] = native_str("floopflarp")
        group = {}

        res = app.post_json("/api/groups", group, headers=headers, expect_errors=True)

        assert res.status_code == 404


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
