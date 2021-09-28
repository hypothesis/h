import base64

import pytest

from h.models.auth_client import GrantType


class TestCreateGroup:
    def test_it_returns_http_200_with_valid_payload(
        self, app, token_auth_header, group_payload
    ):
        res = app.post_json("/api/groups", group_payload, headers=token_auth_header)

        assert res.status_code == 200

    def test_it_ignores_non_whitelisted_fields_in_payload(
        self, app, token_auth_header, group_payload
    ):
        group_payload["organization"] = "foobar"
        group_payload["joinable_by"] = "whoever"

        res = app.post_json("/api/groups", group_payload, headers=token_auth_header)

        assert res.status_code == 200

    def test_it_returns_http_400_with_invalid_payload(self, app, token_auth_header):
        bad_group_payload = {}

        res = app.post_json(
            "/api/groups",
            bad_group_payload,
            headers=token_auth_header,
            expect_errors=True,
        )

        assert res.status_code == 400

    def test_it_returns_http_400_if_groupid_set_on_default_authority(
        self, app, token_auth_header, group_payload
    ):
        group_payload["groupid"] = "group:12345@example.com"

        res = app.post_json(
            "/api/groups", group_payload, headers=token_auth_header, expect_errors=True
        )

        assert res.status_code == 400

    def test_it_returns_http_404_if_no_authenticated_user(
        self, app, auth_client_header, group_payload
    ):
        # FIXME: This should return a 403
        res = app.post_json(
            "/api/groups", group_payload, headers=auth_client_header, expect_errors=True
        )

        assert res.status_code == 404

    @pytest.mark.xfail
    def test_it_returns_http_403_if_no_authenticated_user(
        self, app, auth_client_header, group_payload
    ):
        res = app.post_json(
            "/api/groups", group_payload, headers=auth_client_header, expect_errors=True
        )

        assert res.status_code == 403

    def test_it_allows_auth_client_with_forwarded_user(
        self, app, auth_client_header, third_party_user, group_payload
    ):
        headers = auth_client_header
        headers["X-Forwarded-User"] = third_party_user.userid

        res = app.post_json("/api/groups", group_payload, headers=headers)

        assert res.status_code == 200

    def test_it_allows_groupdid_from_auth_client_with_forwarded_user(
        self, app, auth_client_header, third_party_user
    ):
        headers = auth_client_header
        headers["X-Forwarded-User"] = third_party_user.userid
        group = {"name": "My Group", "groupid": "group:23457456~@thirdparty.com"}

        res = app.post_json("/api/groups", group, headers=headers)
        data = res.json

        assert res.status_code == 200
        assert "groupid" in data
        assert data["groupid"] == "group:23457456~@thirdparty.com"

    def test_it_returns_HTTP_Conflict_if_groupid_is_duplicate(
        self, app, auth_client_header, third_party_user, group_payload
    ):
        group_payload["groupid"] = "group:23456@thirdparty.com"
        headers = auth_client_header
        headers["X-Forwarded-User"] = third_party_user.userid

        app.post_json("/api/groups", group_payload, headers=headers)
        res = app.post_json(
            "/api/groups", group_payload, headers=headers, expect_errors=True
        )

        assert res.status_code == 409

    def test_it_returns_http_404_with_invalid_forwarded_user_format(
        self, app, auth_client_header
    ):
        # FIXME: This should return a 403
        headers = auth_client_header
        headers["X-Forwarded-User"] = "floopflarp"
        group = {}

        res = app.post_json("/api/groups", group, headers=headers, expect_errors=True)

        assert res.status_code == 404

    @pytest.fixture
    def group_payload(self, factories):
        # Create a group we won't save for access to all the nice fakers
        group = factories.Group.build()

        return {"name": group.name}


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
def user_with_token(db_session, factories):
    user = factories.User()
    token = factories.DeveloperToken(userid=user.userid)
    db_session.add(token)
    db_session.commit()
    return (user, token)


@pytest.fixture
def token_auth_header(user_with_token):
    user, token = user_with_token
    return {"Authorization": "Bearer {}".format(token.value)}
