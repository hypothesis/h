from unittest import mock
from unittest.mock import create_autospec

import pytest
from h_assets import Environment
from pyramid import httpexceptions

from h.services.exceptions import ConflictError
from h.services.user_signup import UserSignupService
from h.views import account_signup as views


@pytest.mark.usefixtures("pyramid_config", "routes", "user_signup_service")
class TestSignupController:
    def test_post_returns_errors_when_validation_fails(
        self, invalid_form, pyramid_request, mocker, assets_env
    ):
        pyramid_request.POST = {
            "username": "jane",
            "password": "doe",
            "email": "jane@example.org",
            "privacy_accepted": "true",
            "comms_opt_in": "false",
        }
        mocker.spy(views, "get_csrf_token")
        controller = views.SignupController(pyramid_request)
        controller.form = invalid_form()
        form_errors = {"username": "This username is already taken."}
        form = invalid_form(errors=form_errors)
        controller.form = form

        result = controller.post()

        assert result == {
            "js_config": {
                "styles": assets_env.urls.return_value,
                "csrfToken": views.get_csrf_token.spy_return,
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
        self, form_validating_to, pyramid_request, user_signup_service, datetime
    ):
        controller = views.SignupController(pyramid_request)
        controller.form = form_validating_to(
            {
                "username": "bob",
                "email": "bob@example.com",
                "password": "s3crets",
                "random_other_field": "something else",
                "comms_opt_in": True,
            }
        )

        controller.post()

        user_signup_service.signup.assert_called_with(
            username="bob",
            email="bob@example.com",
            password="s3crets",  # noqa: S106
            privacy_accepted=datetime.datetime.now(datetime.UTC),
            comms_opt_in=True,
        )

    def test_post_does_not_create_user_when_validation_fails(
        self, invalid_form, pyramid_request, user_signup_service
    ):
        controller = views.SignupController(pyramid_request)
        controller.form = invalid_form()

        controller.post()

        assert not user_signup_service.signup.called

    def test_post_displays_heading_and_message_on_success(self, controller):
        result = controller.post()

        assert result["heading"] == "Account registration successful"
        assert result["message"] is None

    def test_post_displays_heading_and_message_on_conflict_error(
        self, controller, user_signup_service
    ):
        user_signup_service.signup.side_effect = ConflictError(
            "The account bob@example.com is already registered."
        )

        result = controller.post()

        assert result["heading"] == "Account already registered"
        assert result["message"] == (
            "The account bob@example.com is already registered."
        )

    def test_get_renders_form_when_not_logged_in(
        self, pyramid_request, mocker, assets_env
    ):
        mocker.spy(views, "get_csrf_token")
        controller = views.SignupController(pyramid_request)
        controller.form.render = mock.Mock()

        assert controller.get() == {
            "js_config": {
                "styles": assets_env.urls.return_value,
                "csrfToken": views.get_csrf_token.spy_return,
            }
        }

    def test_get_redirects_when_logged_in(self, pyramid_config, pyramid_request):
        pyramid_config.testing_securitypolicy("acct:jane@doe.org")
        pyramid_request.user = mock.Mock(username="janedoe")
        controller = views.SignupController(pyramid_request)

        with pytest.raises(httpexceptions.HTTPRedirection):
            controller.get()

    @pytest.fixture
    def controller(self, form_validating_to, pyramid_request):
        controller = views.SignupController(pyramid_request)
        controller.form = form_validating_to(
            {
                "username": "bob",
                "email": "bob@example.com",
                "password": "s3crets",
                "comms_opt_in": True,
            }
        )

        return controller

    @pytest.fixture
    def assets_env(self):
        return create_autospec(Environment, instance=True, spec_set=True)

    @pytest.fixture(autouse=True)
    def pyramid_config(self, pyramid_config, assets_env):
        pyramid_config.registry["assets_env"] = assets_env
        return pyramid_config


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route("activity.user_search", "/users/{username}")
    pyramid_config.add_route("index", "/index")


@pytest.fixture
def user_signup_service(pyramid_config):
    service = mock.create_autospec(UserSignupService, spec_set=True, instance=True)
    pyramid_config.register_service(service, name="user_signup")
    return service


@pytest.fixture
def datetime(patch):
    return patch("h.views.account_signup.datetime")
