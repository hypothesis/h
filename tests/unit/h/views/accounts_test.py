from dataclasses import asdict
from datetime import datetime, timedelta
from unittest import mock
from unittest.mock import create_autospec

import colander
import deform
import pytest
from h_matchers import Any
from pyramid import httpexceptions

from h.assets import Environment
from h.models import Subscriptions
from h.services.email import EmailData, EmailTag, TaskData
from h.tasks import email
from h.views import accounts as views


class FakeForm:
    appstruct = None

    def set_appstruct(self, appstruct):
        self.appstruct = appstruct

    def render(self):
        return self.appstruct


class FakeSerializer:
    pass


@pytest.mark.usefixtures("routes")
class TestBadCSRFTokenHTML:
    def test_it_returns_login_with_root_next_as_default(self, pyramid_request):
        pyramid_request.referer = None
        result = views.bad_csrf_token_html(None, pyramid_request)

        assert result["login_path"] == "/login?next=%2F"

    def test_it_returns_login_with_referer_path_as_next(self, pyramid_request):
        pyramid_request.referer = (
            "http://" + pyramid_request.domain + "/account/settings"
        )

        result = views.bad_csrf_token_html(None, pyramid_request)

        assert result["login_path"] == "/login?next=%2Faccount%2Fsettings"

    def test_it_returns_login_with_root_when_hostnames_are_different(
        self, pyramid_request
    ):
        pyramid_request.domain = "example.org"
        pyramid_request.referer = "http://example.com/account/settings"

        result = views.bad_csrf_token_html(None, pyramid_request)

        assert result["login_path"] == "/login?next=%2F"

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route("login", "/login")


@pytest.mark.usefixtures("routes")
class TestAuthController:
    def test_get(self, pyramid_request, mocker, assets_env):
        mocker.spy(views, "get_csrf_token")

        result = views.AuthController(pyramid_request).get()

        assets_env.urls.assert_called_once_with("forms_css")
        views.get_csrf_token.assert_called_once_with(pyramid_request)
        assert result == {
            "js_config": {
                "styles": assets_env.urls.return_value,
                "csrfToken": views.get_csrf_token.spy_return,
                "features": {
                    "log_in_with_orcid": True,
                    "log_in_with_google": True,
                    "log_in_with_facebook": True,
                },
                "flashMessages": [],
                "form": {
                    "data": {
                        "username": None,
                    }
                },
                "urls": {
                    "login": {
                        provider: pyramid_request.route_url(f"oidc.login.{provider}")
                        for provider in ("facebook", "google", "orcid")
                    }
                },
            }
        }

    def test_get_with_feature_flags_disabled(self, pyramid_request):
        pyramid_request.feature.flags["log_in_with_facebook"] = False
        pyramid_request.feature.flags["log_in_with_google"] = False
        pyramid_request.feature.flags["log_in_with_orcid"] = False

        result = views.AuthController(pyramid_request).get()

        assert result["js_config"]["features"] == {
            "log_in_with_orcid": False,
            "log_in_with_google": False,
            "log_in_with_facebook": False,
        }
        for provider in ("facebook", "google", "orcid"):
            assert provider not in result.get("urls", {}).get("login", {})

    def test_get_with_prefilled_username(self, pyramid_request):
        pyramid_request.GET.add("username", "johnsmith")

        result = views.AuthController(pyramid_request).get()

        assert result["js_config"]["form"]["data"]["username"] == "johnsmith"

    def test_get_for_oauth(self, pyramid_request):
        pyramid_request.params = {"for_oauth": "true"}

        result = views.AuthController(pyramid_request).get()

        assert result["js_config"]["forOAuth"]

    def test_get_with_flash_messages(self, pyramid_request, mocker):
        mocker.spy(views, "get_csrf_token")
        pyramid_request.session.flash("Login successful!", "success")
        pyramid_request.session.flash("Invalid password", "error")

        result = views.AuthController(pyramid_request).get()

        expected_flash_messages = [
            {"type": "success", "message": "Login successful!"},
            {"type": "error", "message": "Invalid password"},
        ]
        assert result["js_config"]["flashMessages"] == expected_flash_messages

    def test_get_flash_messages_consumed_after_get(self, pyramid_request):
        pyramid_request.session.flash("Test message", "success")

        views.AuthController(pyramid_request).get()

        assert pyramid_request.session.peek_flash("success") == []

    def test_get_copies_next_query_param_onto_social_login_urls(self, pyramid_request):
        pyramid_request.params["next"] = "https://example.com/oauth/authorize"

        result = views.AuthController(pyramid_request).get()

        assert result["js_config"]["urls"]["login"] == {
            provider: pyramid_request.route_url(
                f"oidc.login.{provider}",
                _query={"next": pyramid_request.params["next"]},
            )
            for provider in ("facebook", "google", "orcid")
        }

    def test_post_returns_form_when_validation_fails(
        self, invalid_form, pyramid_config, pyramid_request, assets_env, mocker
    ):
        pyramid_request.POST = {"username": "jane", "password": "doe"}
        pyramid_config.testing_securitypolicy(None)  # Logged out
        mocker.spy(views, "get_csrf_token")
        controller = views.AuthController(pyramid_request)
        form_errors = {"username": "Invalid username"}
        form = invalid_form(errors=form_errors)
        controller.form = form

        result = controller.post()

        assert result == {
            "js_config": {
                "styles": assets_env.urls.return_value,
                "csrfToken": views.get_csrf_token.spy_return,
                "form": {
                    "data": pyramid_request.POST,
                    "errors": form_errors,
                },
                "features": {
                    "log_in_with_orcid": True,
                    "log_in_with_google": True,
                    "log_in_with_facebook": True,
                },
                "flashMessages": [],
                "urls": {
                    "login": {
                        provider: pyramid_request.route_url(f"oidc.login.{provider}")
                        for provider in ("facebook", "google", "orcid")
                    }
                },
            }
        }

    def test_post_when_feature_flags_disabled(self, invalid_form, pyramid_request):
        controller = views.AuthController(pyramid_request)
        controller.form = invalid_form(errors={"username": "Invalid username"})
        pyramid_request.feature.flags["log_in_with_facebook"] = False
        pyramid_request.feature.flags["log_in_with_google"] = False
        pyramid_request.feature.flags["log_in_with_orcid"] = False

        result = controller.post()

        assert result["js_config"]["features"] == {
            "log_in_with_orcid": False,
            "log_in_with_google": False,
            "log_in_with_facebook": False,
        }
        for provider in ("facebook", "google", "orcid"):
            assert provider not in result.get("urls", {}).get("login", {})

    def test_post_copies_next_query_param_onto_social_login_urls(
        self, invalid_form, pyramid_request
    ):
        pyramid_request.params["next"] = "https://example.com/oauth/authorize"
        controller = views.AuthController(pyramid_request)
        controller.form = invalid_form(errors={"username": "Invalid username"})

        result = controller.post()

        assert result["js_config"]["urls"]["login"] == {
            provider: pyramid_request.route_url(
                f"oidc.login.{provider}",
                _query={"next": pyramid_request.params["next"]},
            )
            for provider in ("facebook", "google", "orcid")
        }

    def test_post_redirects_when_logged_in(self, pyramid_config, pyramid_request):
        pyramid_config.testing_securitypolicy("acct:jane@doe.org")
        pyramid_request.user = mock.Mock(username="janedoe")

        with pytest.raises(httpexceptions.HTTPFound):
            views.AuthController(pyramid_request).post()

    def test_post_redirects_to_search_page_when_logged_in(
        self, pyramid_config, pyramid_request
    ):
        pyramid_config.testing_securitypolicy("acct:jane@doe.org")
        pyramid_request.user = mock.Mock(username="janedoe")

        with pytest.raises(httpexceptions.HTTPFound) as exc:
            views.AuthController(pyramid_request).post()

        assert exc.value.location == "http://example.com/users/janedoe"

    def test_post_redirects_to_next_param_when_logged_in(
        self, pyramid_config, pyramid_request
    ):
        pyramid_request.params = {"next": "/foo/bar"}
        pyramid_request.user = mock.Mock(username="janedoe")
        pyramid_config.testing_securitypolicy("acct:jane@doe.org")

        with pytest.raises(httpexceptions.HTTPFound) as e:
            views.AuthController(pyramid_request).post()

        assert e.value.location == "/foo/bar"

    def test_post_redirects_when_validation_succeeds(
        self, factories, form_validating_to, pyramid_config, pyramid_request, login
    ):
        pyramid_config.testing_securitypolicy(None)  # Logged out
        controller = views.AuthController(pyramid_request)
        user = factories.User(username="cara")
        pyramid_request.user = user
        controller.form = form_validating_to({"user": user})
        login.return_value = [
            ("headername1", "headervalue1"),
            ("headername2", "headervalue2"),
        ]

        result = controller.post()

        assert isinstance(result, httpexceptions.HTTPFound)
        login.assert_called_once_with(user, pyramid_request)
        assert all(header in result.headerlist for header in login.return_value)

    def test_post_redirects_to_next_param_when_validation_succeeds(
        self, factories, form_validating_to, pyramid_config, pyramid_request
    ):
        pyramid_request.params = {"next": "/foo/bar"}
        pyramid_config.testing_securitypolicy(None)  # Logged out
        controller = views.AuthController(pyramid_request)
        user = factories.User(username="cara")
        pyramid_request.user = user
        controller.form = form_validating_to({"user": user})

        result = controller.post()

        assert isinstance(result, httpexceptions.HTTPFound)
        assert result.location == "/foo/bar"

    @mock.patch("h.views.accounts.LogoutEvent", autospec=True)
    def test_logout_event(self, logoutevent, notify, pyramid_config, pyramid_request):
        pyramid_config.testing_securitypolicy("acct:jane@doe.org")

        views.AuthController(pyramid_request).logout()

        logoutevent.assert_called_with(pyramid_request)
        notify.assert_called_with(logoutevent.return_value)

    def test_logout_invalidates_session(self, pyramid_config, pyramid_request):
        pyramid_request.session["foo"] = "bar"
        pyramid_config.testing_securitypolicy("acct:jane@doe.org")

        views.AuthController(pyramid_request).logout()

        assert "foo" not in pyramid_request.session

    def test_logout_redirects(self, pyramid_request):
        result = views.AuthController(pyramid_request).logout()

        assert isinstance(result, httpexceptions.HTTPFound)

    def test_logout_response_has_forget_headers(self, pyramid_config, pyramid_request):
        pyramid_config.testing_securitypolicy(
            forget_result={"x-erase-fingerprints": "on the hob"}
        )

        result = views.AuthController(pyramid_request).logout()

        assert result.headers["x-erase-fingerprints"] == "on the hob"

    @pytest.fixture
    def assets_env(self):
        return create_autospec(Environment, instance=True, spec_set=True)

    @pytest.fixture(autouse=True)
    def pyramid_config(self, pyramid_config, assets_env):
        pyramid_config.registry["assets_env"] = assets_env
        return pyramid_config

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route("activity.search", "/search")
        pyramid_config.add_route("activity.user_search", "/users/{username}")
        pyramid_config.add_route("forgot_password", "/forgot")
        pyramid_config.add_route("index", "/index")
        pyramid_config.add_route("stream", "/stream")
        pyramid_config.add_route("oidc.login.facebook", "/oidc/login/facebook")
        pyramid_config.add_route("oidc.login.google", "/oidc/login/google")
        pyramid_config.add_route("oidc.login.orcid", "/oidc/login/orcid")
        pyramid_config.add_route("oauth_authorize", "/oauth/authorize")


@pytest.mark.usefixtures(
    "activation_model", "tasks_email", "reset_password_email", "routes"
)
class TestForgotPasswordController:
    def test_post_returns_form_when_validation_fails(
        self, invalid_form, pyramid_request
    ):
        controller = views.ForgotPasswordController(pyramid_request)
        controller.form = invalid_form()

        result = controller.post()

        assert result == {"form": "invalid form"}

    def test_post_creates_no_activations_when_validation_fails(
        self, activation_model, invalid_form, pyramid_request
    ):
        controller = views.ForgotPasswordController(pyramid_request)
        controller.form = invalid_form()

        controller.post()

        assert not activation_model.call_count

    def test_post_generates_mail(
        self,
        reset_password_email,
        factories,
        form_validating_to,
        pyramid_request,
    ):
        pyramid_request.registry.password_reset_serializer = FakeSerializer()
        user = factories.User(username="giraffe", email="giraffe@thezoo.org")
        controller = views.ForgotPasswordController(pyramid_request)
        controller.form = form_validating_to({"user": user})

        controller.post()

        reset_password_email.generate.assert_called_once_with(pyramid_request, user)

    def test_post_sends_mail(
        self,
        form_validating_to,
        tasks_email,
        pyramid_request,
        user,
    ):
        pyramid_request.registry.password_reset_serializer = FakeSerializer()
        controller = views.ForgotPasswordController(pyramid_request)
        controller.form = form_validating_to({"user": user})

        controller.post()

        email_data = EmailData(
            recipients=["giraffe@thezoo.org"],
            subject="Reset yer passwor!",
            body="Text output",
            tag=EmailTag.TEST,
            html="HTML output",
        )
        task_data = TaskData(
            tag=email_data.tag, sender_id=user.id, recipient_ids=[user.id]
        )
        tasks_email.send.delay.assert_called_once_with(
            asdict(email_data), asdict(task_data)
        )

    def test_post_redirects_on_success(
        self, factories, form_validating_to, pyramid_request
    ):
        pyramid_request.registry.password_reset_serializer = FakeSerializer()
        user = factories.User(username="giraffe", email="giraffe@thezoo.org")
        controller = views.ForgotPasswordController(pyramid_request)
        controller.form = form_validating_to({"user": user})

        result = controller.post()

        assert isinstance(result, httpexceptions.HTTPRedirection)

    def test_get_redirects_when_logged_in(self, pyramid_config, pyramid_request):
        pyramid_config.testing_securitypolicy("acct:jane@doe.org")

        with pytest.raises(httpexceptions.HTTPFound):
            views.ForgotPasswordController(pyramid_request).get()

    @pytest.fixture
    def reset_password_email(self, patch):
        reset_password_email = patch("h.views.accounts.reset_password")
        reset_password_email.generate.return_value = EmailData(
            recipients=["giraffe@thezoo.org"],
            subject="Reset yer passwor!",
            body="Text output",
            tag=EmailTag.TEST,
            html="HTML output",
        )
        return reset_password_email

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route("index", "/index")
        pyramid_config.add_route("account_reset", "/account/reset")

    @pytest.fixture
    def user(self, factories, db_session):
        user = factories.User.create(username="giraffe", email="giraffe@thezoo.org")
        db_session.commit()
        return user

    @pytest.fixture
    def pyramid_request(self, pyramid_request, user):
        pyramid_request.user = user
        return pyramid_request


@pytest.mark.usefixtures("routes", "user_password_service")
class TestResetController:
    def test_get_returns_rendered_form(self, pyramid_request, form_validating_to):
        controller = views.ResetController(pyramid_request)
        controller.form = form_validating_to({})

        result = controller.get()

        assert result["form"] == "valid form"
        assert not result["has_code"]

    def test_get_with_prefilled_code_returns_rendered_form(
        self, pyramid_request, form_validating_to
    ):
        pyramid_request.matchdict["code"] = "whatnot"
        controller = views.ResetController(pyramid_request)
        controller.form = form_validating_to({})

        result = controller.get_with_prefilled_code()

        assert result["form"] == "valid form"
        assert result["has_code"] is True

    def test_get_with_prefilled_code_returns_404_if_invalid_code(
        self, pyramid_request, ResetCode, form_validating_to
    ):
        pyramid_request.matchdict["code"] = "whatnot"
        ResetCode.return_value.deserialize.side_effect = colander.Invalid("nope")
        controller = views.ResetController(pyramid_request)
        controller.form = form_validating_to({})

        with pytest.raises(httpexceptions.HTTPNotFound):
            controller.get_with_prefilled_code()

    def test_post_returns_form_when_validation_fails(
        self, invalid_form, pyramid_request
    ):
        controller = views.ResetController(pyramid_request)
        controller.form = invalid_form()

        result = controller.post()

        assert result == {"form": "invalid form"}

    def test_post_sets_user_password_from_form(
        self, factories, form_validating_to, pyramid_request, user_password_service
    ):
        elephant = factories.User()
        controller = views.ResetController(pyramid_request)
        controller.form = form_validating_to({"user": elephant, "password": "s3cure!"})

        controller.post()

        user_password_service.update_password.assert_called_once_with(
            elephant, "s3cure!"
        )

    @mock.patch("h.views.accounts.PasswordResetEvent", autospec=True)
    def test_post_emits_event(
        self, event, factories, form_validating_to, notify, pyramid_request
    ):
        user = factories.User()
        controller = views.ResetController(pyramid_request)
        controller.form = form_validating_to({"user": user, "password": "s3cure!"})

        controller.post()

        event.assert_called_with(pyramid_request, user)
        notify.assert_called_with(event.return_value)

    def test_post_redirects_on_success(
        self, factories, form_validating_to, pyramid_request
    ):
        user = factories.User()
        controller = views.ResetController(pyramid_request)
        controller.form = form_validating_to({"user": user, "password": "s3cure!"})

        result = controller.post()

        assert isinstance(result, httpexceptions.HTTPRedirection)

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route("index", "/index")
        pyramid_config.add_route("login", "/login")
        pyramid_config.add_route("account_reset", "/reset")
        pyramid_config.add_route("account_reset_with_code", "/reset-with-code")

    @pytest.fixture(autouse=True)
    def ResetCode(self, patch):
        return patch("h.views.accounts.ResetCode")


@pytest.mark.usefixtures(
    "ActivationEvent", "activation_model", "notify", "routes", "user_model"
)
class TestActivateController:
    def test_get_when_not_logged_in_404s_if_id_not_int(self, pyramid_request):
        pyramid_request.matchdict = {"id": "abc", "code": "abc456"}  # Not an int.

        with pytest.raises(httpexceptions.HTTPNotFound):
            views.ActivateController(pyramid_request).get_when_not_logged_in()

    def test_get_when_not_logged_in_looks_up_activation_by_code(
        self, activation_model, pyramid_request, user_model
    ):
        pyramid_request.matchdict = {"id": "123", "code": "abc456"}
        user_model.get_by_activation.return_value.id = 123

        views.ActivateController(pyramid_request).get_when_not_logged_in()

        activation_model.get_by_code.assert_called_with(pyramid_request.db, "abc456")

    def test_get_when_not_logged_in_redirects_if_activation_not_found(
        self, activation_model, pyramid_request
    ):
        # If the activation code doesn't match any activation then we redirect to
        # the front page and flash a message suggesting that they may already be
        # activated and can log in.

        # This happens if a user clicks on an activation link from an email after
        # they've already been activated, for example.

        # (This also happens if users visit a bogus activation URL, but we're
        # happy to do this same redirect in that edge case.)
        pyramid_request.matchdict = {"id": "123", "code": "abc456"}
        activation_model.get_by_code.return_value = None

        result = views.ActivateController(pyramid_request).get_when_not_logged_in()

        assert isinstance(result, httpexceptions.HTTPFound)
        assert result.location == "http://example.com/login"
        assert pyramid_request.session.peek_flash("error") == [
            Any.string.containing(
                "We didn't recognize that activation link. Have you already activated "
            ),
        ]

    def test_get_when_not_logged_in_looks_up_user_by_activation(
        self, activation_model, pyramid_request, user_model
    ):
        pyramid_request.matchdict = {"id": "123", "code": "abc456"}
        user_model.get_by_activation.return_value.id = 123

        views.ActivateController(pyramid_request).get_when_not_logged_in()

        user_model.get_by_activation.assert_called_once_with(
            pyramid_request.db, activation_model.get_by_code.return_value
        )

    def test_get_when_not_logged_in_404s_if_user_not_found(
        self, pyramid_request, user_model
    ):
        pyramid_request.matchdict = {"id": "123", "code": "abc456"}
        user_model.get_by_activation.return_value = None

        with pytest.raises(httpexceptions.HTTPNotFound):
            views.ActivateController(pyramid_request).get_when_not_logged_in()

    def test_get_when_not_logged_in_404s_if_user_id_does_not_match_hash(
        self, pyramid_request, user_model
    ):
        # We don't want to let a user with a valid hash activate a different
        # user's account!
        pyramid_request.matchdict = {"id": "123", "code": "abc456"}
        user_model.get_by_activation.return_value.id = 2  # Not the same id.

        with pytest.raises(httpexceptions.HTTPNotFound):
            views.ActivateController(pyramid_request).get_when_not_logged_in()

    def test_get_when_not_logged_in_successful_activates_user(
        self, pyramid_request, user_model
    ):
        pyramid_request.matchdict = {"id": "123", "code": "abc456"}
        pyramid_request.db.delete = mock.create_autospec(
            pyramid_request.db.delete, return_value=None
        )
        user_model.get_by_activation.return_value.id = 123

        views.ActivateController(pyramid_request).get_when_not_logged_in()

        user_model.get_by_activation.return_value.activate.assert_called_once_with()

    def test_get_when_not_logged_in_successful_flashes_message(
        self, pyramid_request, user_model
    ):
        pyramid_request.matchdict = {"id": "123", "code": "abc456"}
        user_model.get_by_activation.return_value.id = 123

        views.ActivateController(pyramid_request).get_when_not_logged_in()

        assert pyramid_request.session.peek_flash("success") == [
            Any.string.containing("Your account has been activated")
        ]

    def test_get_when_not_logged_in_successful_creates_ActivationEvent(
        self, pyramid_request, user_model, ActivationEvent
    ):
        pyramid_request.matchdict = {"id": "123", "code": "abc456"}
        user_model.get_by_activation.return_value.id = 123

        views.ActivateController(pyramid_request).get_when_not_logged_in()

        ActivationEvent.assert_called_once_with(
            pyramid_request, user_model.get_by_activation.return_value
        )

    def test_get_when_not_logged_in_successful_notifies(
        self, notify, pyramid_request, user_model, ActivationEvent
    ):
        pyramid_request.matchdict = {"id": "123", "code": "abc456"}
        user_model.get_by_activation.return_value.id = 123

        views.ActivateController(pyramid_request).get_when_not_logged_in()

        notify.assert_called_once_with(ActivationEvent.return_value)

    def test_get_when_logged_in_already_logged_in_when_id_not_an_int(
        self, pyramid_request
    ):
        pyramid_request.user = mock.Mock(id=123, spec=["id"])
        pyramid_request.matchdict = {"id": "abc", "code": "abc456"}  # Not an int.

        with pytest.raises(httpexceptions.HTTPNotFound):
            views.ActivateController(pyramid_request).get_when_logged_in()

    def test_get_when_logged_in_already_logged_in_to_same_account(
        self, pyramid_request
    ):
        pyramid_request.user = mock.Mock(id=123, spec=["id"])
        pyramid_request.matchdict = {"id": "123", "code": "abc456"}

        result = views.ActivateController(pyramid_request).get_when_logged_in()
        success_flash = pyramid_request.session.peek_flash("success")

        assert isinstance(result, httpexceptions.HTTPFound)
        assert success_flash
        assert success_flash[0].startswith(
            "Your account has been activated and you're logged in"
        )

    def test_get_when_logged_in_already_logged_in_to_different_account(
        self, pyramid_request
    ):
        pyramid_request.user = mock.Mock(id=124, spec=["id"])
        pyramid_request.matchdict = {"id": "123", "code": "abc456"}

        result = views.ActivateController(pyramid_request).get_when_logged_in()
        error_flash = pyramid_request.session.peek_flash("error")

        assert isinstance(result, httpexceptions.HTTPFound)
        assert error_flash
        assert error_flash[0].startswith(
            "You're already logged in to a different account"
        )

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route("index", "/index")
        pyramid_config.add_route("login", "/login")
        pyramid_config.add_route("logout", "/logout")


@pytest.mark.usefixtures(
    "routes", "user_password_service", "feature_service", "oidc_service"
)
class TestAccountController:
    def test_get_returns_email_if_set(self, pyramid_request):
        pyramid_request.user = mock.Mock()
        pyramid_request.create_form.return_value = mock.Mock()
        user = pyramid_request.user
        user.email = "jims@example.com"

        result = views.AccountController(pyramid_request).get()
        assert result["email"] == "jims@example.com"

    def test_get_returns_empty_string_if_email_not_set(self, pyramid_request):
        pyramid_request.user = mock.Mock()
        pyramid_request.create_form.return_value = mock.Mock()
        user = pyramid_request.user
        user.email = None

        result = views.AccountController(pyramid_request).get()
        assert not result["email"]

    def test_get_returns_orcid_data(
        self, pyramid_request, feature_service, oidc_service
    ):
        pyramid_request.registry.settings["orcid_host"] = "https://sandbox.orcid.org"
        oidc_service.get_identity.return_value.provider_unique_id = (
            "test_provider_unique_id"
        )
        feature_service.enabled.return_value = True

        result = views.AccountController(pyramid_request).get()

        assert result["orcid"] == "test_provider_unique_id"
        assert (
            result["orcid_url"] == "https://sandbox.orcid.org/test_provider_unique_id"
        )

    def test_post_email_form_with_valid_data_changes_email(
        self, form_validating_to, pyramid_request
    ):
        controller = views.AccountController(pyramid_request)
        controller.email_form = form_validating_to({"email": "new_email_address"})

        controller.post_email_form()

        assert pyramid_request.user.email == "new_email_address"

    def test_post_email_form_with_invalid_data_does_not_change_email(
        self, invalid_form, pyramid_request
    ):
        controller = views.AccountController(pyramid_request)
        controller.email_form = invalid_form()
        original_email = pyramid_request.user.email

        controller.post_email_form()

        assert pyramid_request.user.email == original_email

    def test_post_email_form_with_invalid_data_returns_template_data(
        self, invalid_form, pyramid_request
    ):
        controller = views.AccountController(pyramid_request)
        controller.email_form = invalid_form()

        result = controller.post_email_form()

        assert result == {
            "email": pyramid_request.user.email,
            "email_form": controller.email_form.render(),
            "password_form": controller.password_form.render(),
            "log_in_with_orcid": False,
            "orcid": None,
            "orcid_url": None,
            "log_in_with_google": False,
            "google_id": None,
            "log_in_with_facebook": False,
            "facebook_id": None,
        }

    def test_post_password_form_with_valid_data_changes_password(
        self, form_validating_to, pyramid_request, user_password_service
    ):
        controller = views.AccountController(pyramid_request)
        controller.addpassword_form = form_validating_to(
            {"new_password": "my_new_password"}
        )

        controller.post_password_form()

        user_password_service.update_password.assert_called_once_with(
            pyramid_request.user, "my_new_password"
        )

    def test_post_password_form_with_invalid_data_does_not_change_password(
        self, invalid_form, pyramid_request, user_password_service
    ):
        controller = views.AccountController(pyramid_request)
        controller.addpassword_form = invalid_form()

        controller.post_password_form()

        assert not user_password_service.update_password.called

    def test_post_password_form_with_invalid_data_returns_template_data(
        self, invalid_form, pyramid_request
    ):
        controller = views.AccountController(pyramid_request)
        controller.addpassword_form = invalid_form()

        result = controller.post_password_form()

        assert result == {
            "email": pyramid_request.user.email,
            "email_form": controller.email_form.render(),
            "password_form": controller.addpassword_form.render(),
            "log_in_with_orcid": False,
            "orcid": None,
            "orcid_url": None,
            "log_in_with_google": False,
            "google_id": None,
            "log_in_with_facebook": False,
            "facebook_id": None,
        }

    @pytest.fixture
    def pyramid_request(self, factories, pyramid_request):
        pyramid_request.POST = {}
        pyramid_request.user = factories.User()
        return pyramid_request

    @pytest.fixture
    def feature_service(self, feature_service):
        feature_service.enabled.return_value = False
        return feature_service

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route("account", "/my/account")


class TestNotificationsController:
    def test_get(self, controller, authenticated_user, subscription_service):
        result = controller.get()

        subscription_service.get_all_subscriptions.assert_called_once_with(
            user_id=authenticated_user.userid
        )
        controller.form.set_appstruct.assert_called_once_with(
            {"notifications": {"reply"}}
        )
        assert "form" in result
        assert result["user_has_email_address"] == authenticated_user.email

    def test_get_if_user_has_no_email_address(self, controller, authenticated_user):
        authenticated_user.email = None

        result = controller.get()

        assert result == {"user_has_email_address": None}

    @pytest.mark.parametrize("set_active", (True, False))
    def test_post(
        self,
        controller,
        authenticated_user,
        form_validating_to,
        subscription_service,
        set_active,
    ):
        subscription = subscription_service.get_all_subscriptions.return_value[0]
        subscription.active = not set_active
        controller.form = form_validating_to(
            {"notifications": {"reply"} if set_active else set()}
        )

        result = controller.post()

        subscription_service.get_all_subscriptions.assert_called_once_with(
            user_id=authenticated_user.userid
        )
        assert subscription.active if set_active else not subscription.active
        # This appears to be testing `h.form.handle_form_submission()`
        assert isinstance(result, httpexceptions.HTTPFound)

    def test_post_with_invalid_data(self, controller, authenticated_user, invalid_form):
        authenticated_user.email = None
        controller.form = invalid_form()

        result = controller.post()

        assert result == {"user_has_email_address": None}

    @pytest.fixture
    def controller(self, pyramid_request, form_validating_to):
        controller = views.NotificationsController(pyramid_request)
        controller.form = form_validating_to({})

        return controller

    @pytest.fixture(autouse=True)
    def authenticated_user(self, pyramid_config, pyramid_request, factories):
        authenticated_user = factories.User(email="email@example.com")
        pyramid_config.testing_securitypolicy(userid=authenticated_user.userid)
        pyramid_request.user = authenticated_user

        return authenticated_user

    @pytest.fixture(autouse=True)
    def subscription_service(self, subscription_service, factories):
        subscription_service.get_all_subscriptions.return_value = [
            factories.Subscriptions(type=Subscriptions.Type.REPLY.value, active=True)
        ]
        return subscription_service


@pytest.mark.usefixtures("pyramid_config")
class TestEditProfileController:
    def test_get_reads_user_properties(self, pyramid_request):
        pyramid_request.user = mock.Mock()
        pyramid_request.create_form.return_value = FakeForm()
        user = pyramid_request.user
        user.display_name = "Jim Smith"
        user.description = "Job Description"
        user.orcid = "ORCID iD"
        user.uri = "http://foo.org"
        user.location = "Paris"

        result = views.EditProfileController(pyramid_request).get()

        assert result == {
            "form": {
                "display_name": "Jim Smith",
                "description": "Job Description",
                "orcid": "ORCID iD",
                "link": "http://foo.org",
                "location": "Paris",
            }
        }

    def test_post_sets_user_properties(self, form_validating_to, pyramid_request):
        pyramid_request.user = mock.Mock()
        user = pyramid_request.user

        ctrl = views.EditProfileController(pyramid_request)
        ctrl.form = form_validating_to(
            {
                "display_name": "Jim Smith",
                "description": "Job Description",
                "orcid": "ORCID iD",
                "link": "http://foo.org",
                "location": "Paris",
            }
        )
        ctrl.post()

        assert user.display_name == "Jim Smith"
        assert user.description == "Job Description"
        assert user.orcid == "ORCID iD"
        assert user.uri == "http://foo.org"
        assert user.location == "Paris"


@pytest.mark.usefixtures("authenticated_userid", "developer_token_service")
class TestDeveloperController:
    def test_get_fetches_token(
        self, controller, developer_token_service, authenticated_userid
    ):
        controller.get()

        developer_token_service.fetch.assert_called_once_with(authenticated_userid)

    def test_get_returns_token_for_authenticated_user(
        self, controller, developer_token_service
    ):
        assert controller.get() == {
            "token": developer_token_service.fetch.return_value.value
        }

    def test_get_returns_empty_context_for_missing_token(
        self, controller, developer_token_service
    ):
        developer_token_service.fetch.return_value = None

        assert controller.get() == {}

    def test_post_fetches_token(
        self, controller, developer_token_service, authenticated_userid
    ):
        controller.post()

        developer_token_service.fetch.assert_called_once_with(authenticated_userid)

    def test_post_regenerates_token_when_found(
        self, controller, developer_token_service
    ):
        controller.post()

        developer_token_service.regenerate.assert_called_once_with(
            developer_token_service.fetch.return_value
        )

    def test_post_returns_regenerated_token_when_found(
        self, controller, developer_token_service
    ):
        result = controller.post()

        assert result == {
            "token": developer_token_service.regenerate.return_value.value
        }

    def test_post_creates_new_token_when_not_found(
        self, controller, developer_token_service, authenticated_userid
    ):
        developer_token_service.fetch.return_value = None

        controller.post()

        developer_token_service.create.assert_called_once_with(authenticated_userid)

    def test_post_returns_new_token_when_not_found(
        self, controller, developer_token_service
    ):
        developer_token_service.fetch.return_value = None

        result = controller.post()

        assert result == {"token": developer_token_service.create.return_value.value}

    @pytest.fixture
    def controller(self, pyramid_request):
        return views.DeveloperController(pyramid_request)

    @pytest.fixture
    def authenticated_userid(self, pyramid_config):
        userid = "acct:jane@example.com"
        pyramid_config.testing_securitypolicy(userid)
        return userid


class TestDeleteController:
    def test_get(
        self,
        authenticated_user,
        controller,
        factories,
        pyramid_request,
        schemas,
        matchers,
    ):
        oldest_annotation = factories.Annotation(
            userid=authenticated_user.userid,
            created=datetime(1970, 1, 1),  # noqa: DTZ001
        )
        newest_annotation = factories.Annotation(
            userid=authenticated_user.userid,
            created=datetime(1990, 1, 1),  # noqa: DTZ001
        )
        # An annotation by another user. This shouldn't be counted.
        factories.Annotation(created=oldest_annotation.created - timedelta(days=1))
        # A deleted annotation. This shouldn't be counted.
        factories.Annotation(
            userid=authenticated_user.userid,
            deleted=True,
            created=newest_annotation.created + timedelta(days=1),
        )

        template_vars = controller.get()

        schemas.DeleteAccountSchema.assert_called_once_with()
        schemas.DeleteAccountSchema.return_value.bind.assert_called_with(
            request=pyramid_request
        )
        pyramid_request.create_form.assert_called_once_with(
            schemas.DeleteAccountSchema.return_value.bind.return_value,
            buttons=Any.iterable.comprised_of(matchers.InstanceOf(deform.Button)),
            formid="delete",
            back_link={
                "href": "http://example.com/account/settings",
                "text": matchers.InstanceOf(str),
            },
        )
        pyramid_request.create_form.return_value.render.assert_called_once_with()

        assert template_vars == {
            "count": 2,
            "oldest": oldest_annotation.created,
            "newest": newest_annotation.created,
            "form": pyramid_request.create_form.return_value.render.return_value,
        }

    def test_get_when_user_has_no_annotations(self, controller, pyramid_request):
        template_vars = controller.get()

        assert template_vars == {
            "count": 0,
            "oldest": None,
            "newest": None,
            "form": pyramid_request.create_form.return_value.render.return_value,
        }

    def test_post(self, controller, form, pyramid_request, schemas, matchers):
        result = controller.post()

        schemas.DeleteAccountSchema.assert_called_once_with()
        schemas.DeleteAccountSchema.return_value.bind.assert_called_with(
            request=pyramid_request
        )
        pyramid_request.create_form.assert_called_once_with(
            schemas.DeleteAccountSchema.return_value.bind.return_value,
            buttons=Any.iterable.comprised_of(matchers.InstanceOf(deform.Button)),
            formid="delete",
            back_link={
                "href": "http://example.com/account/settings",
                "text": matchers.InstanceOf(str),
            },
        )
        form.handle_form_submission.assert_called_once_with(
            pyramid_request,
            pyramid_request.create_form.return_value,
            on_success=controller.delete_user,
            on_failure=controller.template_data,
            flash_success=False,
        )
        assert result == form.handle_form_submission.return_value

    def test_delete_user(
        self,
        authenticated_user,
        controller,
        pyramid_request,
        user_delete_service,
        matchers,
    ):
        response = controller.delete_user(mock.sentinel.appstruct)

        user_delete_service.delete_user.assert_called_once_with(
            authenticated_user,
            requested_by=authenticated_user,
            tag=pyramid_request.matched_route.name,
        )
        assert response == matchers.InstanceOf(
            httpexceptions.HTTPFound,
            location="http://example.com/account/deleted",
        )

    @pytest.fixture(autouse=True)
    def authenticated_user(self, factories, pyramid_config, pyramid_request):
        authenticated_user = factories.User.build()
        pyramid_config.testing_securitypolicy(authenticated_user.userid)
        pyramid_request.user = authenticated_user
        return authenticated_user

    @pytest.fixture
    def controller(self, pyramid_request):
        return views.DeleteController(pyramid_request)

    @pytest.fixture(autouse=True)
    def routes(self, pyramid_config):
        pyramid_config.add_route("account", "/account/settings")
        pyramid_config.add_route("account_delete", "/account/delete")
        pyramid_config.add_route("account_deleted", "/account/deleted")

    @pytest.fixture(autouse=True)
    def form(self, patch):
        return patch("h.views.accounts.form")


def test_account_deleted(pyramid_request):
    assert views.account_deleted(pyramid_request) == {}


@pytest.fixture
def user_model(patch):
    return patch("h.models.User")


@pytest.fixture
def activation_model(patch):
    return patch("h.models.Activation")


@pytest.fixture
def ActivationEvent(patch):
    return patch("h.views.accounts.ActivationEvent")


@pytest.fixture
def tasks_email(patch):
    mock = patch("h.views.accounts.email")
    mock.send.delay = create_autospec(email.send.run)
    return mock


@pytest.fixture(autouse=True)
def LoginSchema(patch):
    return patch("h.views.accounts.LoginSchema")


@pytest.fixture(autouse=True)
def schemas(patch):
    return patch("h.views.accounts.schemas")


@pytest.fixture(autouse=True)
def login(patch):
    return patch("h.views.accounts.login")
