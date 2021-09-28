import base64

import pytest

from h.models.auth_client import GrantType


class TestReadUser:
    def test_it_returns_http_404_if_auth_client_missing(self, app, user):
        url = f"/api/users/{user.userid}"

        res = app.get(url, expect_errors=True)

        assert res.status_code == 404

    def test_it_returns_user_when_successful(self, app, auth_client_header, user):
        url = f"/api/users/{user.userid}"

        res = app.get(url, headers=auth_client_header)

        assert res.json_body["email"] == user.email
        assert res.json_body["display_name"] == user.display_name


class TestCreateUser:
    def test_it_returns_http_200_when_successful(
        self, app, auth_client_header, user_payload
    ):
        res = app.post_json("/api/users", user_payload, headers=auth_client_header)

        assert res.status_code == 200

    def test_it_returns_404_if_missing_auth_client(self, app, user_payload):
        # FIXME: This should return a 403; our exception views squash it into a 404
        res = app.post_json("/api/users", user_payload, expect_errors=True)

        assert res.status_code == 404

    @pytest.mark.xfail
    def test_it_returns_403_if_missing_auth_client(self, app, user_payload):
        res = app.post_json("/api/users", user_payload, expect_errors=True)

        assert res.status_code == 403

    def test_it_returns_400_if_invalid_payload(
        self, app, user_payload, auth_client_header
    ):
        del user_payload["username"]

        res = app.post_json(
            "/api/users", user_payload, headers=auth_client_header, expect_errors=True
        )

        assert res.status_code == 400

    def test_it_returns_400_if_authority_param_missing(
        self, app, user_payload, auth_client_header
    ):
        del user_payload["authority"]

        res = app.post_json(
            "/api/users", user_payload, headers=auth_client_header, expect_errors=True
        )

        assert res.status_code == 400

    def test_it_returns_400_if_authority_mismatch(
        self, app, user_payload, auth_client_header
    ):
        user_payload["authority"] = "mismatch.com"

        res = app.post_json(
            "/api/users", user_payload, headers=auth_client_header, expect_errors=True
        )

        assert res.status_code == 400
        assert (
            res.json_body["reason"]
            == "authority 'mismatch.com' does not match client authority"
        )

    def test_it_returns_409_if_user_conflict(self, app, auth_client_header, user):
        existing_user_payload = self.payload_for_user(user)

        # user fixture creates user with conflicting username/authority combo
        res = app.post_json(
            "/api/users",
            existing_user_payload,
            headers=auth_client_header,
            expect_errors=True,
        )

        assert res.status_code == 409

    @pytest.fixture
    def user_payload(self, factories):
        # Create a user we won't save just to get access to all the nice fakers
        return self.payload_for_user(factories.User.build())

    def payload_for_user(self, user):
        return {
            "username": user.username,
            "email": user.email,
            "authority": user.authority,
        }


class TestUpdateUser:
    def test_it_returns_http_200_when_successful(
        self, app, auth_client_header, user, patch_user_payload
    ):
        url = f"/api/users/{user.username}"

        res = app.patch_json(url, patch_user_payload, headers=auth_client_header)

        assert res.status_code == 200

    def test_it_ignores_unrecognized_parameters(self, app, auth_client_header, user):
        url = f"/api/users/{user.username}"
        payload = {"email": "fingers@bonzo.com", "authority": "nicetry.com"}

        res = app.patch_json(url, payload, headers=auth_client_header)

        assert res.status_code == 200
        assert res.json_body["email"] == "fingers@bonzo.com"
        assert res.json_body["authority"] == "example.com"

    def test_it_returns_updated_user_when_successful(
        self, app, auth_client_header, user, patch_user_payload
    ):
        url = f"/api/users/{user.username}"

        res = app.patch_json(url, patch_user_payload, headers=auth_client_header)

        assert res.json_body["email"] == patch_user_payload["email"]
        assert res.json_body["display_name"] == patch_user_payload["display_name"]

    def test_it_returns_http_404_if_auth_client_missing(
        self, app, user, patch_user_payload
    ):
        url = f"/api/users/{user.username}"

        res = app.patch_json(url, patch_user_payload, expect_errors=True)

        assert res.status_code == 404

    def test_it_returns_http_404_if_user_not_in_client_authority(
        self, app, auth_client_header, user, patch_user_payload, db_session
    ):
        user.authority = "somewhere.com"
        db_session.commit()
        url = f"/api/users/{user.username}"

        res = app.patch_json(
            url, patch_user_payload, headers=auth_client_header, expect_errors=True
        )

        assert res.status_code == 404


@pytest.fixture
def patch_user_payload(factories):
    # Create a user we won't save just to get access to all the nice fakers
    temp_user = factories.User.build()

    return {"email": temp_user.email, "display_name": temp_user.display_name}


@pytest.fixture
def auth_client(db_session, factories):
    auth_client = factories.ConfidentialAuthClient(
        authority="example.com", grant_type=GrantType.client_credentials
    )
    db_session.commit()
    return auth_client


@pytest.fixture
def auth_client_header(auth_client):
    user_pass = f"{auth_client.id}:{auth_client.secret}"
    encoded = base64.standard_b64encode(user_pass.encode("utf-8"))
    return {"Authorization": f"Basic {encoded.decode('ascii')}"}


@pytest.fixture
def user(db_session, factories):
    user = factories.User.create()
    db_session.commit()

    return user
