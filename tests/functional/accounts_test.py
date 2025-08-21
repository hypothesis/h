import json

import pytest
from sqlalchemy import select

from h.models import User, UserIdentity
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
            "flashMessages": [],
            "forms": {
                "email": {"data": {}, "errors": {}},
                "password": {"data": {}, "errors": {}},
            },
            "routes": {
                "identity_delete": "http://localhost/account/settings/identity",
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


class TestDeleteIdentity:
    def test_it(
        self,
        app,
        delete_params,
        db_session,
        user,
        google_identity,
        facebook_identity,
        orcid_identity,
    ):
        app.post("/account/settings/identity", delete_params(google_identity))

        assert set(
            db_session.scalars(
                select(UserIdentity).where(UserIdentity.user_id == user.id)
            )
        ) == {facebook_identity, orcid_identity}

    def test_unknown_provider(self, app, delete_params, google_identity):
        params = delete_params(google_identity)
        params["provider"] = "unknown"

        app.post("/account/settings/identity", params, status=404)

    def test_no_csrf_token(self, app, delete_params, google_identity):
        params = delete_params(google_identity)
        del params["csrf_token"]

        app.post("/account/settings/identity", params, status=403)

    def test_invalid_csrf_token(self, app, delete_params, google_identity):
        params = delete_params(google_identity)
        params["csrf_token"] = "invalid"  # noqa: S105

        app.post("/account/settings/identity", params, status=403)

    def test_not_logged_in(self, app, delete_params, google_identity):
        app.get("/logout")

        app.post(
            "/account/settings/identity", delete_params(google_identity), status=404
        )

    def test_only_login_method(
        self,
        app,
        db_session,
        user,
        delete_params,
        google_identity,
        facebook_identity,
        orcid_identity,
    ):
        user.password = None
        db_session.delete(facebook_identity)
        db_session.delete(orcid_identity)
        db_session.commit()

        app.post("/account/settings/identity", delete_params(google_identity))

        assert (
            db_session.scalars(
                select(UserIdentity).where(UserIdentity.id == google_identity.id)
            ).one_or_none()
            == google_identity
        )

    @pytest.fixture
    def delete_params(self, csrf_token):
        def delete_params(identity):
            """Return the correct POST params to delete `identity`."""
            return {
                "csrf_token": csrf_token,
                "provider": identity.provider.split(".")[0],
                "provider_unique_id": identity.provider_unique_id,
            }

        return delete_params

    @pytest.fixture
    def google_identity(self, add_identity):
        return add_identity(IdentityProvider.GOOGLE)

    @pytest.fixture
    def facebook_identity(self, add_identity):
        return add_identity(IdentityProvider.FACEBOOK)

    @pytest.fixture
    def orcid_identity(self, add_identity):
        return add_identity(IdentityProvider.ORCID)

    @pytest.fixture
    def add_identity(self, db_session, user, factories):
        def add_identity(provider):
            identity = factories.UserIdentity(provider=provider, user_id=user.id)
            db_session.commit()
            return identity

        return add_identity

    @pytest.fixture
    def csrf_token(self, app):
        return js_config_from(app.get("/account/settings"))["csrfToken"]

    @pytest.fixture
    def user(self, db_session, factories):
        user = factories.User(
            # Password is "pass".
            password="$2b$12$21I1LjTlGJmLXzTDrQA8gusckjHEMepTmLY5WN3Kx8hSaqEEKj9V6"  # noqa: S106
        )
        db_session.commit()
        return user

    @pytest.fixture(autouse=True)
    def log_in(self, app, user):
        app.post(
            "/login",
            params={
                "username": user.username,
                "password": "pass",
                "csrf_token": js_config_from(app.get("/login"))["csrfToken"],
            },
        )


def js_config_from(response):
    return json.loads(response.html.find("script", class_="js-config").text)
