from datetime import UTC
from unittest import mock

import pytest
from freezegun import freeze_time
from pyramid import httpexceptions

from h.services.exceptions import ConflictError
from h.views import account_signup as views


@pytest.mark.usefixtures("pyramid_config", "user_signup_service")
class TestSignupViews:
    def test_post_returns_errors_when_validation_fails(
        self, invalid_form, pyramid_request, get_csrf_token
    ):
        pyramid_request.POST = {
            "username": "jane",
            "password": "doe",
            "email": "jane@example.org",
            "privacy_accepted": "true",
            "comms_opt_in": "false",
        }
        signup_views = views.SignupViews(pyramid_request)
        signup_views.form = invalid_form()
        form_errors = {"username": "This username is already taken."}
        form = invalid_form(errors=form_errors)
        signup_views.form = form

        result = signup_views.post()

        assert result == {
            "js_config": {
                "csrfToken": get_csrf_token.return_value,
                "formErrors": form_errors,
                "formData": {
                    "username": "jane",
                    "password": "doe",
                    "email": "jane@example.org",
                    "privacy_accepted": True,
                    "comms_opt_in": False,
                },
            }
        }

    def test_post_creates_user_from_form_data(
        self, form_validating_to, pyramid_request, user_signup_service, frozen_time
    ):
        signup_views = views.SignupViews(pyramid_request)
        signup_views.form = form_validating_to(
            {
                "username": "bob",
                "email": "bob@example.com",
                "password": "s3crets",
                "random_other_field": "something else",
                "comms_opt_in": True,
            }
        )

        signup_views.post()

        user_signup_service.signup.assert_called_with(
            username="bob",
            email="bob@example.com",
            password="s3crets",  # noqa: S106
            privacy_accepted=frozen_time.astimezone(UTC),
            comms_opt_in=True,
        )

    def test_post_does_not_create_user_when_validation_fails(
        self, invalid_form, pyramid_request, user_signup_service
    ):
        signup_views = views.SignupViews(pyramid_request)
        signup_views.form = invalid_form()

        signup_views.post()

        assert not user_signup_service.signup.called

    def test_post_displays_heading_and_message_on_success(self, signup_views):
        result = signup_views.post()

        assert result["heading"] == "Account registration successful"
        assert result["message"] is None

    def test_post_displays_heading_and_message_on_conflict_error(
        self, signup_views, user_signup_service
    ):
        user_signup_service.signup.side_effect = ConflictError(
            "The account bob@example.com is already registered."
        )

        result = signup_views.post()

        assert result["heading"] == "Account already registered"
        assert result["message"] == (
            "The account bob@example.com is already registered."
        )

    def test_get_renders_form_when_not_logged_in(self, pyramid_request, get_csrf_token):
        signup_views = views.SignupViews(pyramid_request)
        signup_views.form.render = mock.Mock()

        assert signup_views.get() == {
            "js_config": {"csrfToken": get_csrf_token.return_value}
        }

    def test_get_redirects_when_logged_in(self, pyramid_config, pyramid_request):
        pyramid_config.testing_securitypolicy("acct:jane@doe.org")
        pyramid_request.user = mock.Mock(username="janedoe")
        signup_views = views.SignupViews(pyramid_request)

        with pytest.raises(httpexceptions.HTTPRedirection):
            signup_views.get()

    @pytest.fixture
    def signup_views(self, form_validating_to, pyramid_request):
        signup_views = views.SignupViews(pyramid_request)
        signup_views.form = form_validating_to(
            {
                "username": "bob",
                "email": "bob@example.com",
                "password": "s3crets",
                "comms_opt_in": True,
            }
        )

        return signup_views

    @pytest.fixture
    def frozen_time(self):
        with freeze_time("2012-01-14 03:21:34") as frozen_time_factory:
            yield frozen_time_factory()

    @pytest.fixture(autouse=True)
    def routes(self, pyramid_config):
        pyramid_config.add_route("activity.user_search", "/users/{username}")
        pyramid_config.add_route("index", "/index")


@pytest.fixture(autouse=True)
def get_csrf_token(patch):
    return patch("h.views.account_signup.get_csrf_token")
