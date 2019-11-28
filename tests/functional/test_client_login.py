from urllib.parse import parse_qs, urlparse

import pytest
from h_matchers import Any
from kombu.utils import json

from h.models.auth_client import GrantType


class TestLoginFlow:
    def test_authorisation_redirects_to_login_if_logged_out(self, app, params):
        response = app.get("/oauth/authorize", params=params, status=302)

        # Check we are redirected to the login page
        location = response.headers["Location"]
        raw_url, query = self._parse_url(location)
        assert raw_url == "http://localhost/login"

        # Check the next location for the login page contains all the same
        # details as our original request
        next_url, query = self._parse_url(query["next"])
        assert next_url == "http://localhost/oauth/authorize"
        assert query == params

    def test_authorisation_presents_form_if_logged_in(self, app, user, params):
        self.login(app, user)
        response = app.get("/oauth/authorize", params=params, status=200)

        js_settings = self._approve_authorize_request(response)

        assert js_settings == {
            "code": Any.string(),
            "origin": "http://localhost:5000",
            "state": params["state"],
        }

    def test_the_code_from_auth_can_be_exchanged(self, app, user, params):
        self.login(app, user)
        response = app.get("/oauth/authorize", params=params, status=200)
        js_settings = self._approve_authorize_request(response)
        code = js_settings["code"]

        response = app.post(
            "/api/token",
            params={
                "client_id": params["client_id"],
                "code": code,
                "grant_type": GrantType.authorization_code.value,
            },
            status=200,
        )

        assert response.headers["Content-Type"] == Any.string.matching(
            "application/json"
        )
        assert response.json == Any.dict.containing(
            {
                "token_type": "Bearer",
                "access_token": Any.string(),
                "refresh_token": Any.string(),
            }
        )

    @classmethod
    def _approve_authorize_request(cls, response):
        # Check this is the kind of response we expect
        assert response.headers["Content-Type"] == Any.string.matching("^text/html")
        assert response.text == Any.string.containing(
            "requesting access to your Hypothesis account"
        )

        result = response.form.submit()
        js_settings = result.html.find("script", class_="js-hypothesis-settings")

        return json.loads(js_settings.text)

    @classmethod
    def _parse_url(cls, url):
        url = urlparse(url)
        query = parse_qs(url.query)
        url = url._replace(query=None)

        query = {key: value[0] for key, value in query.items()}

        return url.geturl(), query

    @classmethod
    def login(cls, app, user):
        res = app.get("/login")
        res.form["username"] = user.username
        res.form["password"] = "pass"
        res.form.submit()

    @pytest.fixture
    def params(self, authclient):
        return {
            "client_id": authclient.id,
            "origin": "http://example.com/some_path",
            "response_mode": "web_message",
            "response_type": "code",
            "state": "80750c691329aedd",
        }

    @pytest.fixture
    def authclient(self, db_session, factories):
        authclient = factories.ConfidentialAuthClient(
            grant_type=GrantType.authorization_code,
            secret=None,
            response_type="code",
            trusted=False,
            redirect_uri="{current_scheme}://{current_host}:5000/app.html",
        )
        db_session.commit()
        return authclient

    @pytest.fixture
    def user(self, db_session, factories):
        # Password is 'pass'
        user = factories.User(
            password="$2b$12$21I1LjTlGJmLXzTDrQA8gusckjHEMepTmLY5WN3Kx8hSaqEEKj9V6"
        )
        db_session.commit()
        return user
