from dataclasses import asdict
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest import mock
from unittest.mock import call, create_autospec, sentinel

import colander
import deform
import pytest
from deform import ValidationFailure
from h_matchers import Any
from pyramid import httpexceptions
from pyramid.csrf import get_csrf_token
from sqlalchemy import select

from h.assets import Environment
from h.models import Subscriptions, UserIdentity
from h.models.user_identity import IdentityProvider
from h.services.email import EmailData, EmailTag, TaskData
from h.tasks import email
from h.views import accounts as views


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
        pyramid_config.add_route("signup", "/signup")


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
                        "username_or_email": pyramid_request.route_url("login"),
                        **{
                            provider: pyramid_request.route_url(
                                f"oidc.login.{provider}"
                            )
                            for provider in ("facebook", "google", "orcid")
                        },
                    },
                    "signup": pyramid_request.route_url("signup"),
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
            "username_or_email": pyramid_request.route_url(
                "login", _query={"next": pyramid_request.params["next"]}
            ),
            **{
                provider: pyramid_request.route_url(
                    f"oidc.login.{provider}",
                    _query={"next": pyramid_request.params["next"]},
                )
                for provider in ("facebook", "google", "orcid")
            },
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
                        "username_or_email": pyramid_request.route_url("login"),
                        **{
                            provider: pyramid_request.route_url(
                                f"oidc.login.{provider}"
                            )
                            for provider in ("facebook", "google", "orcid")
                        },
                    },
                    "signup": pyramid_request.route_url("signup"),
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
            "username_or_email": pyramid_request.route_url(
                "login", _query={"next": pyramid_request.params["next"]}
            ),
            **{
                provider: pyramid_request.route_url(
                    f"oidc.login.{provider}",
                    _query={"next": pyramid_request.params["next"]},
                )
                for provider in ("facebook", "google", "orcid")
            },
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

    @mock.patch("h.views.helpers.LogoutEvent", autospec=True)
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
        pyramid_config.add_route("login", "/login")
        pyramid_config.add_route("signup", "/signup")
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


@pytest.mark.usefixtures("user_password_service", "oidc_service")
class TestAccountController:
    @pytest.mark.parametrize("current_email_address", [None, "test_email@example.com"])
    @pytest.mark.parametrize("user_has_password", [True, False])
    def test_get(
        self,
        controller,
        pyramid_request,
        user,
        current_email_address,
        user_has_password,
    ):
        user.email = current_email_address
        if user_has_password:
            user.password = "password"  # noqa: S105
        else:
            user.password = None

        response = controller.get()

        assert response == {
            "js_config": {
                "context": {
                    "identities": {
                        "facebook": {"connected": False},
                        "google": {"connected": False},
                        "orcid": {"connected": False},
                    },
                    "user": {
                        "email": current_email_address,
                        "has_password": user_has_password,
                    },
                },
                "csrfToken": get_csrf_token(pyramid_request),
                "features": {
                    "log_in_with_facebook": True,
                    "log_in_with_google": True,
                    "log_in_with_orcid": True,
                },
                "flashMessages": [],
                "forms": {
                    "email": {"data": {}, "errors": {}},
                    "password": {"data": {}, "errors": {}},
                },
                "routes": {
                    "oidc.connect.facebook": pyramid_request.route_url(
                        "oidc.connect.facebook"
                    ),
                    "oidc.connect.google": pyramid_request.route_url(
                        "oidc.connect.google"
                    ),
                    "oidc.connect.orcid": pyramid_request.route_url(
                        "oidc.connect.orcid"
                    ),
                    "identity_delete": pyramid_request.route_url("account_identity"),
                },
            }
        }

    def test_get_with_flash_messages(self, controller, pyramid_request):
        pyramid_request.session.flash("Something was successful", "success")
        pyramid_request.session.flash("Something failed", "error")

        response = controller.get()

        assert response["js_config"]["flashMessages"] == [
            {"type": "success", "message": "Something was successful"},
            {"type": "error", "message": "Something failed"},
        ]

    def test_get_with_feature_flags_disabled(self, controller, pyramid_request):
        pyramid_request.feature.flags["log_in_with_google"] = False
        pyramid_request.feature.flags["log_in_with_facebook"] = False
        pyramid_request.feature.flags["log_in_with_orcid"] = False

        response = controller.get()

        assert response["js_config"]["features"] == {
            "log_in_with_facebook": False,
            "log_in_with_google": False,
            "log_in_with_orcid": False,
        }
        assert "identities" not in response["js_config"]["context"]
        for route in [
            f"oidc.connect.{provider.name.lower()}" for provider in IdentityProvider
        ]:
            assert route not in response["js_config"].get("routes", {})

    def test_get_when_provider_accounts_connected(
        self, controller, oidc_service, pyramid_request, factories, user, db_session
    ):
        db_session.flush()
        identities = {}
        for provider in IdentityProvider:
            identities[provider] = factories.UserIdentity(
                user_id=user.id, provider=provider
            )
        oidc_service.get_identity.side_effect = identities.values()

        response = controller.get()

        assert oidc_service.get_identity.call_args_list == [
            call(user, provider) for provider in IdentityProvider
        ]
        expected_identities = {}
        for provider in IdentityProvider:
            expected_identity = {
                "connected": True,
                "provider_unique_id": identities[provider].provider_unique_id,
                "email": identities[provider].email,
            }
            if provider == IdentityProvider.ORCID:
                expected_identity["url"] = (
                    f"https://sandbox.orcid.org/{identities[IdentityProvider.ORCID].provider_unique_id}"
                )
            expected_identities[provider.name.lower()] = expected_identity
        assert response["js_config"]["context"]["identities"] == expected_identities
        assert response["js_config"]["routes"] == {
            "identity_delete": pyramid_request.route_url("account_identity"),
            **{
                f"oidc.connect.{provider.name.lower()}": pyramid_request.route_url(
                    f"oidc.connect.{provider.name.lower()}"
                )
                for provider in IdentityProvider
            },
        }

    @pytest.mark.parametrize(
        "user_has_password,schema",
        [
            (False, "EmailAddSchema"),
            (True, "EmailChangeSchema"),
        ],
    )
    def test_post_email_form_valid(
        self,
        controller,
        pyramid_request,
        schemas,
        matchers,
        user_has_password,
        user,
        schema,
    ):
        if user_has_password:
            user.password = "pass"  # noqa: S105
        else:
            user.password = None
        pyramid_request.create_form.return_value.validate.return_value = {
            "email": "new_email@example.com"
        }

        response = controller.post_email_form()

        schema = getattr(schemas, schema)
        schema.assert_called_once_with()
        schema.return_value.bind.assert_called_once_with(request=pyramid_request)
        pyramid_request.create_form.assert_called_once_with(
            schema.return_value.bind.return_value
        )
        pyramid_request.create_form.return_value.validate.assert_called_once_with(
            PostItemsMatcher(pyramid_request.POST.items())
        )
        assert pyramid_request.user.email == "new_email@example.com"
        assert pyramid_request.session.peek_flash("success") == [
            "Email address changed"
        ]
        assert matchers.Redirect302To(pyramid_request.route_url("account")) == response

    def test_post_email_form_invalid(self, controller, pyramid_request):
        exception = pyramid_request.create_form.return_value.validate.side_effect = (
            ValidationFailure(sentinel.field, sentinel.cstruct, sentinel.error)
        )

        with pytest.raises(ValidationFailure) as exc_info:
            controller.post_email_form()

        assert exc_info.value == exception

    @pytest.mark.parametrize(
        "user_has_password,schema",
        [
            (False, "PasswordAddSchema"),
            (True, "PasswordChangeSchema"),
        ],
    )
    def test_post_password_form_valid(
        self,
        controller,
        pyramid_request,
        schemas,
        matchers,
        user,
        user_password_service,
        user_has_password,
        schema,
    ):
        if user_has_password:
            user.password = "password"  # noqa: S105
        else:
            user.password = None
        pyramid_request.create_form.return_value.validate.return_value = {
            "new_password": "test_new_password"
        }

        response = controller.post_password_form()

        schema = getattr(schemas, schema)
        schema.assert_called_once_with()
        schema.return_value.bind.assert_called_once_with(request=pyramid_request)
        pyramid_request.create_form.assert_called_once_with(
            schema.return_value.bind.return_value
        )
        pyramid_request.create_form.return_value.validate.assert_called_once_with(
            PostItemsMatcher(pyramid_request.POST.items())
        )
        user_password_service.update_password.assert_called_once_with(
            user, "test_new_password"
        )
        assert pyramid_request.session.peek_flash("success") == ["Password changed"]
        assert matchers.Redirect302To(pyramid_request.route_url("account")) == response

    def test_post_password_form_invalid(self, controller, pyramid_request):
        exception = pyramid_request.create_form.return_value.validate.side_effect = (
            ValidationFailure(sentinel.field, sentinel.cstruct, sentinel.error)
        )

        with pytest.raises(ValidationFailure) as exc_info:
            controller.post_password_form()

        assert exc_info.value == exception

    @pytest.mark.parametrize("formid", ["email", "password"])
    def test_validation_failure(self, controller, pyramid_request, formid):
        pyramid_request.params = {
            "__formid__": formid,
            "email": "invalid_email",
            "password": "pass",
            "new_password": "new_pass",
            "new_password_confirm": "new_pass_confirm",
        }
        errors = {
            "email": "invalid email address",
            "password": "wrong password",
            "new_password": "invalid password",
            "new_pass_confirm": "password don't match",
        }
        controller.context = SimpleNamespace(
            error=SimpleNamespace(asdict=lambda: errors)
        )

        response = controller.validation_failure()

        assert pyramid_request.response.status_int == 400
        assert response["js_config"]["forms"][formid] == {
            "data": {"email": "invalid_email"},
            "errors": errors,
        }

    @pytest.fixture
    def controller(self, pyramid_request):
        return views.AccountController(sentinel.context, pyramid_request)

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def pyramid_request(self, pyramid_request, user):
        pyramid_request.user = user
        return pyramid_request

    @pytest.fixture(autouse=True)
    def routes(self, pyramid_config):
        pyramid_config.add_route("oidc.connect.google", "/oidc/connect/google")
        pyramid_config.add_route("oidc.connect.facebook", "/oidc/connect/facebook")
        pyramid_config.add_route("oidc.connect.orcid", "/oidc/connect/orcid")
        pyramid_config.add_route("account", "/account/settings")
        pyramid_config.add_route("account_identity", "/account/settings/identity")

    @pytest.fixture(autouse=True)
    def pyramid_settings(self, pyramid_settings):
        pyramid_settings["orcid_host"] = "https://sandbox.orcid.org"
        return pyramid_settings

    @pytest.fixture
    def oidc_service(self, oidc_service):
        oidc_service.get_identity.return_value = None
        return oidc_service


class TestDeleteIdentity:
    def test_it(self, db_session, user, pyramid_request, factories, matchers):
        db_session.flush()
        google_identity = factories.UserIdentity(
            provider=IdentityProvider.GOOGLE, user_id=user.id
        )
        facebook_identity = factories.UserIdentity(
            provider=IdentityProvider.FACEBOOK, user_id=user.id
        )
        orcid_identity = factories.UserIdentity(
            provider=IdentityProvider.ORCID, user_id=user.id
        )
        pyramid_request.params = {
            "provider": "google",
            "provider_unique_id": google_identity.provider_unique_id,
        }

        response = views.delete_identity(pyramid_request)

        assert set(
            db_session.scalars(
                select(UserIdentity).where(UserIdentity.user_id == user.id)
            )
        ) == {facebook_identity, orcid_identity}
        assert pyramid_request.session.peek_flash("success") == [
            f"{google_identity.provider} disconnected"
        ]
        assert matchers.Redirect302To(pyramid_request.route_url("account")) == response

    def test_unknown_provider(self, pyramid_request):
        pyramid_request.params = {
            "provider": "unknown_provider",
            "provider_unique_id": "unknown_provider_unique_id",
        }

        with pytest.raises(httpexceptions.HTTPNotFound):
            views.delete_identity(pyramid_request)

    def test_provider_not_connected(self, pyramid_request, matchers):
        pyramid_request.params = {"provider": "google", "provider_unique_id": "123"}

        response = views.delete_identity(pyramid_request)

        assert pyramid_request.session.peek_flash("error") == [
            "google.com not connected. Did you already disconnect this provider in another tab?"
        ]
        assert matchers.Redirect302To(pyramid_request.route_url("account")) == response

    def test_no_other_login_methods(
        self, pyramid_request, user, matchers, db_session, factories
    ):
        user.password = None
        db_session.flush()
        google_identity = factories.UserIdentity(
            provider=IdentityProvider.GOOGLE, user_id=user.id
        )
        pyramid_request.params = {
            "provider": "google",
            "provider_unique_id": google_identity.provider_unique_id,
        }

        response = views.delete_identity(pyramid_request)

        assert (
            db_session.scalars(
                select(UserIdentity).where(UserIdentity.user_id == user.id)
            ).one()
            == google_identity
        )
        assert pyramid_request.session.peek_flash("error") == [
            "Can't disconnect account:"
            f" {google_identity.provider} is currently the only way to log in to your Hypothesis account."
            " Connect another account or add a password first."
        ]
        assert matchers.Redirect302To(pyramid_request.route_url("account")) == response

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def pyramid_request(self, pyramid_request, user):
        pyramid_request.user = user
        return pyramid_request

    @pytest.fixture(autouse=True)
    def routes(self, pyramid_config):
        pyramid_config.add_route("account", "/account/settings")


class TestNotificationsController:
    def test_get(self, controller, authenticated_user, subscription_service):
        result = controller.get()

        subscription_service.get_all_subscriptions.assert_called_once_with(
            user_id=authenticated_user.userid
        )

        assert "js_config" in result
        assert result["js_config"]["hasEmail"] is True
        assert result["js_config"]["form"]["data"]["reply"] is True
        assert result["js_config"]["form"]["data"]["mention"] is False
        assert result["js_config"]["form"]["data"]["moderation"] is False

    def test_get_if_user_has_no_email_address(self, controller, authenticated_user):
        authenticated_user.email = None

        result = controller.get()

        assert "js_config" in result
        assert result["js_config"]["hasEmail"] is False

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
        controller.form = form_validating_to({"reply": set_active})

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

        assert "js_config" in result
        assert result["js_config"]["hasEmail"] is False

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
            factories.Subscriptions(type=Subscriptions.Type.REPLY.value, active=True),
            factories.Subscriptions(
                type=Subscriptions.Type.MENTION.value, active=False
            ),
            # MODERATION subscription is missing, so implicitly false.
        ]
        return subscription_service


@pytest.mark.usefixtures("pyramid_config")
class TestEditProfileController:
    def test_get_reads_user_properties(self, pyramid_request, mocker):
        mocker.spy(views, "get_csrf_token")
        pyramid_request.user = mock.Mock()
        pyramid_request.create_form.return_value = create_autospec(
            deform.Form, instance=True, spec_set=True
        )
        user = pyramid_request.user
        user.display_name = "Jim Smith"
        user.description = "Job Description"
        user.orcid = "ORCID iD"
        user.uri = "http://foo.org"
        user.location = "Paris"

        result = views.EditProfileController(pyramid_request).get()

        views.get_csrf_token.assert_called_once_with(pyramid_request)
        assert result == {
            "js_config": {
                "csrfToken": views.get_csrf_token.spy_return,
                "features": {},
                "flashMessages": [],
                "form": {
                    "data": {
                        "display_name": "Jim Smith",
                        "description": "Job Description",
                        "orcid": "ORCID iD",
                        "link": "http://foo.org",
                        "location": "Paris",
                    },
                    "errors": {},
                },
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

    def test_post_returns_errors_on_validation_failure(
        self, pyramid_request, invalid_form, mocker
    ):
        mocker.spy(views, "get_csrf_token")
        pyramid_request.POST = {"display_name": "invalid", "description": "test"}

        pyramid_request.user = mock.Mock()
        user = pyramid_request.user
        user.display_name = "Original Name"
        user.description = "Original Description"
        user.orcid = "Original ORCID"
        user.uri = "http://original.com"
        user.location = "Original Location"

        ctrl = views.EditProfileController(pyramid_request)
        ctrl.form = invalid_form({"display_name": "Display name is invalid"})

        result = ctrl.post()

        views.get_csrf_token.assert_called_once_with(pyramid_request)
        assert result == {
            "js_config": {
                "csrfToken": views.get_csrf_token.spy_return,
                "features": {},
                "flashMessages": [],
                "form": {
                    "data": {
                        "display_name": "invalid",
                        "description": "test",
                        "orcid": "Original ORCID",
                        "link": "http://original.com",
                        "location": "Original Location",
                    },
                    "errors": {"display_name": "Display name is invalid"},
                },
            }
        }


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
            "js_config": {
                "features": {},
                "token": developer_token_service.fetch.return_value.value,
            }
        }

    def test_get_returns_empty_context_for_missing_token(
        self, controller, developer_token_service
    ):
        developer_token_service.fetch.return_value = None

        assert controller.get() == {"js_config": {"features": {}}}

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
            "js_config": {
                "features": {},
                "token": developer_token_service.regenerate.return_value.value,
            }
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

        assert result == {
            "js_config": {
                "features": {},
                "token": developer_token_service.create.return_value.value,
            }
        }

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

    def test_get_when_user_has_no_password(
        self, authenticated_user, controller, pyramid_request, schemas, matchers
    ):
        authenticated_user.password = None

        controller.get()

        schemas.DeleteAccountSchemaNoPassword.assert_called_once_with()
        schemas.DeleteAccountSchemaNoPassword.return_value.bind.assert_called_with(
            request=pyramid_request
        )
        pyramid_request.create_form.assert_called_once_with(
            schemas.DeleteAccountSchemaNoPassword.return_value.bind.return_value,
            buttons=Any.iterable.comprised_of(matchers.InstanceOf(deform.Button)),
            formid="delete",
            back_link={
                "href": "http://example.com/account/settings",
                "text": matchers.InstanceOf(str),
            },
        )

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

    def test_post_when_user_has_no_password(
        self, controller, pyramid_request, schemas, matchers, authenticated_user
    ):
        authenticated_user.password = None

        controller.post()

        schemas.DeleteAccountSchemaNoPassword.assert_called_once_with()
        schemas.DeleteAccountSchemaNoPassword.return_value.bind.assert_called_with(
            request=pyramid_request
        )
        pyramid_request.create_form.assert_called_once_with(
            schemas.DeleteAccountSchemaNoPassword.return_value.bind.return_value,
            buttons=Any.iterable.comprised_of(matchers.InstanceOf(deform.Button)),
            formid="delete",
            back_link={
                "href": "http://example.com/account/settings",
                "text": matchers.InstanceOf(str),
            },
        )

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
        authenticated_user = factories.User.build(password="pass")  # noqa: S106
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


class PostItemsMatcher:
    def __init__(self, items):
        self.items = items

    def __eq__(self, other):
        return list(other) == list(self.items)
