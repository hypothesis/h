# -*- coding: utf-8 -*-
"""Functional tests for getting and using OAuth 2 access and refresh tokens."""

import calendar
import datetime

import jwt
import pytest

from h.models.auth_client import GrantType


class TestOAuth:
    def test_getting_an_access_token(self, app, authclient, userid):
        """Test using grant tokens and access tokens."""
        # Test using a grant token to get an access token.
        response = self.get_access_token(app, authclient, userid)
        access_token = response["access_token"]

        self.assert_is_authorized(app, userid, access_token)

    def test_request_fails_if_access_token_wrong(self, app, authclient, userid):
        self.assert_is_not_authorised(app, access_token="wrong")

    def test_request_fails_if_access_token_expired(
        self, app, authclient, db_session, factories, userid
    ):
        token = factories.DeveloperToken(
            expires=datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        )
        token = token.value
        db_session.commit()

        self.assert_is_not_authorised(app, token)

    def test_using_a_refresh_token(self, app, authclient, userid):
        """Get a new access token by POSTing a refresh token to /api/token."""
        # Start by getting an access token and refresh token.
        response = self.get_access_token(app, authclient, userid)
        old_access_token = response["access_token"]
        refresh_token = response["refresh_token"]

        # Use the refresh token to get a new access token.
        response = app.post(
            "/api/token",
            {"grant_type": "refresh_token", "refresh_token": refresh_token},
        )
        new_access_token = response.json_body["access_token"]

        # Test that the new access token works.
        self.assert_is_authorized(app, userid, new_access_token)

        # Test that the old access token still works, too.
        self.assert_is_authorized(app, userid, old_access_token)

    def test_refresh_token_request_fails_if_refresh_token_wrong(
        self, app, authclient, userid
    ):
        app.post(
            "/api/token",
            {"grant_type": "refresh_token", "refresh_token": "wrong"},
            status=400,
        )

    def test_refresh_token_request_fails_if_token_expired(
        self, app, authclient, db_session, factories, userid
    ):
        token = factories.DeveloperToken(
            expires=datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        )
        refresh_token = token.refresh_token
        db_session.commit()

        app.post(
            "/api/token",
            {"grant_type": "refresh_token", "refresh_token": refresh_token},
            status=400,
        )

    def test_you_cannot_use_a_refresh_token_to_authenticate_api_requests(
        self, app, authclient, userid
    ):
        response = self.get_access_token(app, authclient, userid)
        refresh_token = response["refresh_token"]

        self.assert_is_not_authorised(app, access_token=refresh_token)

    def test_oauth_authorize_redirects(self, app, auth_code_authclient):
        app.get("/oauth/authorize", {
            "client_id": auth_code_authclient.id,
            "origin": "http://example.com",
            "response_mode": "web_message",
            "response_type": "code",
            "state": "80750c691329aedd"
        }, status=302)

    def test_revoke_token(self, app, authclient, userid):
        response = self.get_access_token(app, authclient, userid)
        refresh_token = response["refresh_token"]
        access_token = response["access_token"]

        headers = {"Authorization": f"Bearer {access_token}"}

        # Check the token works before we revoke it
        self.assert_is_authorized(app, userid, access_token=access_token)

        app.post("/oauth/revoke", {"token": refresh_token}, headers=headers, status=200)

        # Check the token doesn't work after
        self.assert_is_not_authorised(app, access_token=access_token)

    @pytest.mark.parametrize(
        "method, path", [("POST", "/api/token"), ("POST", "/oauth/revoke")]
    )
    def test_oauth_routes_support_cors_preflight(self, app, method, path):
        app.options(
            path,
            headers={
                "Origin": "https://third-party-client.herokuapp.com",
                "Access-Control-Request-Method": str(method),
            },
            status=200,
        )

    def assert_is_authorized(self, app, userid, access_token):
        results = app.get(
            "/api/profile",
            headers={"Authorization": f"Bearer {access_token}"},
            status=200,
        )

        assert results.json_body["userid"] == userid

    def assert_is_not_authorised(self, app, access_token):
        headers = {"Authorization": f"Bearer {access_token}"}
        app.get("/api/debug-token", headers=headers, status=401)

        results = app.get("/api/profile", headers=headers, status=200)

        assert results.json_body["userid"] is None

    def get_access_token(self, app, authclient, userid):
        """Get an access token by POSTing a grant token to /api/token."""
        claims = {
            "iss": authclient.id,
            "aud": "localhost",
            "sub": userid,
            "nbf": self.epoch(),
            "exp": self.epoch(delta=datetime.timedelta(minutes=5)),
        }
        response = app.post(
            "/api/token",
            {
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": jwt.encode(claims, authclient.secret),
            },
        )
        return response.json_body

    def epoch(self, delta=None):
        """Get a Unix timestamp for the current time, with optional offset."""
        timestamp = datetime.datetime.utcnow()

        if delta is not None:
            timestamp = timestamp + delta

        return calendar.timegm(timestamp.utctimetuple())

    @pytest.fixture
    def authclient(self, db_session, factories):
        authclient = factories.ConfidentialAuthClient(
            grant_type=GrantType.jwt_bearer,
        )
        db_session.commit()
        return authclient

    @pytest.fixture
    def auth_code_authclient(self, db_session, factories):
        authclient = factories.ConfidentialAuthClient(
            grant_type=GrantType.authorization_code,
            secret=None,
            response_type="code",
            trusted=False,
            redirect_uri="{current_scheme}://{current_host}:5000/app.html"
        )
        db_session.commit()
        return authclient

    @pytest.fixture
    def userid(self, db_session, factories):
        user = factories.User()
        db_session.commit()
        return user.userid
