import json

import pytest

from h.models import User
from h.models.user_identity import IdentityProvider


class TestAccountSettings:
    """Tests for the /account/settings page."""

    @pytest.mark.usefixtures("logged_in")
    def test_get(self, app, user, matchers):
        response = app.get("/account/settings", status=200)

        assert js_config_from(response) == {
            "context": {"user": {"email": user.email, "has_password": True}},
            "csrfToken": matchers.InstanceOf(str),
            "features": {
                f"log_in_with_{provider.name.lower()}": False
                for provider in IdentityProvider
            },
            "forms": {
                "email": {"data": {}, "errors": {}},
                "password": {"data": {}, "errors": {}},
            },
        }

    def test_get_not_logged_in(self, app):
        app.get("/account/settings", status=404)

    @pytest.mark.usefixtures("logged_in")
    def test_change_email(self, app, user, db_session, change_email, password):
        response = app.get("/account/settings")
        csrf_token = js_config_from(response)["csrfToken"]

        response = change_email(
            {
                "email": "zirk-kaic-vuft@example.com",
                "password": password,
                "csrf_token": csrf_token,
            }
        )

        db_session.expire(user)
        assert (
            db_session.get(
                User,
                user.id,
            ).email
            == "zirk-kaic-vuft@example.com"
        )
        assert response.status_int == 302
        assert response.location == "http://localhost/account/settings"

    @pytest.mark.usefixtures("logged_in")
    @pytest.mark.parametrize(
        "params,data,errors",
        [
            (
                {"email": "invalid", "password": "pass"},
                {"email": "invalid"},
                {"email": "Invalid email address."},
            ),
            (
                {"email": "uh-pond-vaid@example.com", "password": "wrong"},
                {"email": "uh-pond-vaid@example.com"},
                {"password": "Wrong password."},
            ),
        ],
    )
    def test_change_email_invalid(self, app, change_email, params, data, errors):
        response = app.get("/account/settings")
        params["csrf_token"] = js_config_from(response)["csrfToken"]

        response = change_email(params, status=400)

        assert js_config_from(response)["forms"]["email"] == {
            "data": data,
            "errors": errors,
        }

    @pytest.mark.usefixtures("logged_in")
    def test_change_email_no_csrf_token(self, change_email, password):
        change_email(
            {
                "email": "gu-prek-chud@example.com",
                "password": password,
            },
            status=403,
        )

    @pytest.mark.usefixtures("logged_in")
    def test_change_email_not_logged_in(self, app, change_email, password):
        response = app.get("/account/settings")
        csrf_token = js_config_from(response)["csrfToken"]
        app.get("/logout")

        change_email(
            {
                "email": "yoft-skib-zoc@example.com",
                "password": password,
                "csrf_token": csrf_token,
            },
            status=404,
        )

    @pytest.mark.usefixtures("logged_in")
    def test_change_password(self, app, change_password, password):
        response = app.get("/account/settings")
        csrf_token = js_config_from(response)["csrfToken"]

        response = change_password(
            {
                "password": password,
                "new_password": "new_password",
                "new_password_confirm": "new_password",
                "csrf_token": csrf_token,
            }
        )

        assert response.status_int == 302
        assert response.location == "http://localhost/account/settings"

    @pytest.mark.usefixtures("logged_in")
    @pytest.mark.parametrize(
        "params,errors",
        [
            (
                {
                    "password": "wrong",
                    "new_password": "new_password",
                    "new_password_confirm": "new_password",
                },
                {"password": "Wrong password."},
            ),
            (
                {
                    "password": "pass",
                    "new_password": "pass",
                    "new_password_confirm": "pass",
                },
                {"new_password": "Must be 8 characters or more."},
            ),
            (
                {
                    "password": "pass",
                    "new_password": "new_password",
                    "new_password_confirm": "different",
                },
                {"new_password_confirm": "The passwords must match."},
            ),
        ],
    )
    def test_change_password_invalid(self, app, change_password, params, errors):
        response = app.get("/account/settings")
        params["csrf_token"] = js_config_from(response)["csrfToken"]

        response = change_password(params, status=400)

        assert js_config_from(response)["forms"]["password"] == {
            "data": {},
            "errors": errors,
        }

    @pytest.mark.usefixtures("logged_in")
    def test_change_password_no_csrf_token(self, change_password, password):
        change_password(
            {
                "password": password,
                "new_password": "new_password",
                "new_password_confirm": "new_password",
            },
            status=403,
        )

    @pytest.mark.usefixtures("logged_in")
    def test_change_password_not_logged_in(self, app, change_password, password):
        response = app.get("/account/settings")
        csrf_token = js_config_from(response)["csrfToken"]
        app.get("/logout")

        change_password(
            {
                "password": password,
                "new_password": "new_password",
                "new_password_confirm": "new_password",
                "csrf_token": csrf_token,
            },
            status=404,
        )

    @pytest.fixture
    def change_email(self, app):
        def change_email(params, status=None):
            params["__formid__"] = "email"
            return app.post("/account/settings", params=params, status=status)

        return change_email

    @pytest.fixture
    def change_password(self, app):
        def change_password(params, status=None):
            params["__formid__"] = "password"
            return app.post("/account/settings", params=params, status=status)

        return change_password

    @pytest.fixture
    def password(self):
        return "pass"

    @pytest.fixture
    def user(self, db_session, factories):
        # Password is 'pass'
        user = factories.User(
            # This is `password` (above) encrypted.
            password="$2b$12$21I1LjTlGJmLXzTDrQA8gusckjHEMepTmLY5WN3Kx8hSaqEEKj9V6"  # noqa: S106
        )
        db_session.commit()
        return user

    @pytest.fixture
    def logged_in(self, app, user, password):
        app.post(
            "/login",
            params={
                "username": user.username,
                "password": password,
                "csrf_token": js_config_from(app.get("/login"))["csrfToken"],
            },
        )


def js_config_from(response):
    return json.loads(response.html.find("script", class_="js-config").text)
