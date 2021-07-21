import pytest


class TestAccountSettings:
    """Tests for the /account/settings page."""

    def test_submit_email_form_without_xhr_returns_full_html_page(self, app):
        res = app.get("/account/settings")

        email_form = res.forms["email"]
        email_form["email"] = "new_email1@example.com"
        email_form["password"] = "pass"

        res = email_form.submit().follow()

        assert res.text.startswith("<!DOCTYPE html>")

    def test_submit_email_form_with_xhr_returns_partial_html_snippet(self, app):
        res = app.get("/account/settings")

        email_form = res.forms["email"]
        email_form["email"] = "new_email2@example.com"
        email_form["password"] = "pass"

        res = email_form.submit(xhr=True, status=200)

        assert res.text.strip("\n").startswith("<form")

    def test_submit_email_form_with_xhr_returns_plain_text(self, app):
        res = app.get("/account/settings")

        email_form = res.forms["email"]
        email_form["email"] = "new_email3@example.com"
        email_form["password"] = "pass"

        res = email_form.submit(xhr=True)

        assert res.content_type == "text/plain"

    def test_submit_password_form_without_xhr_returns_full_html_page(self, app):
        res = app.get("/account/settings")

        password_form = res.forms["password"]
        password_form["password"] = "pass"
        password_form["new_password"] = "new_password"
        password_form["new_password_confirm"] = "new_password"

        res = password_form.submit().follow()

        assert res.text.startswith("<!DOCTYPE html>")

    def test_submit_password_form_with_xhr_returns_partial_html_snippet(self, app):
        res = app.get("/account/settings")

        password_form = res.forms["password"]
        password_form["password"] = "pass"
        password_form["new_password"] = "new_password"
        password_form["new_password_confirm"] = "new_password"

        res = password_form.submit(xhr=True)

        assert res.text.strip("\n").startswith("<form")

    def test_submit_password_form_with_xhr_returns_plain_text(self, app):
        res = app.get("/account/settings")

        password_form = res.forms["password"]
        password_form["password"] = "pass"
        password_form["new_password"] = "new_password"
        password_form["new_password_confirm"] = "new_password"

        res = password_form.submit(xhr=True)

        assert res.content_type == "text/plain"

    def test_submit_invalid_password_form_with_xhr_returns_400(self, app):
        res = app.get("/account/settings")

        password_form = res.forms["password"]
        password_form["password"] = "pass"
        password_form["new_password"] = "new_password"
        password_form["new_password_confirm"] = "WRONG"

        password_form.submit(xhr=True, status=400)

    @pytest.fixture
    def user(self, db_session, factories):
        # Password is 'pass'
        user = factories.User(
            password="$2b$12$21I1LjTlGJmLXzTDrQA8gusckjHEMepTmLY5WN3Kx8hSaqEEKj9V6"
        )
        db_session.commit()
        return user

    @pytest.fixture
    def app(self, app, user):
        res = app.get("/login")
        res.form["username"] = user.username
        res.form["password"] = "pass"
        res.form.submit()
        return app
