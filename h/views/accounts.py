from dataclasses import asdict
from typing import Any
from urllib.parse import urlparse, urlunparse

import colander
import deform
from markupsafe import Markup
from pyramid import httpexceptions, security
from pyramid.config import not_
from pyramid.csrf import get_csrf_token
from pyramid.exceptions import BadCSRFToken
from pyramid.view import exception_view_config, view_config, view_defaults
from sqlalchemy import func, select

from h import accounts, form, i18n, models, session
from h.accounts import schemas
from h.accounts.events import ActivationEvent, LogoutEvent, PasswordResetEvent
from h.emails import reset_password
from h.models import Annotation, UserIdentity
from h.models.user_identity import IdentityProvider
from h.schemas.forms.accounts import (
    EditProfileSchema,
    ForgotPasswordSchema,
    LoginSchema,
    ResetCode,
    ResetPasswordSchema,
)
from h.services import OIDCService, SubscriptionService
from h.services.email import TaskData
from h.tasks import email
from h.util.view import json_view
from h.views.account_signup import inject_login_urls
from h.views.helpers import login

_ = i18n.TranslationString


# A little helper to ensure that session data is returned in every ajax
# response payload.
def ajax_payload(request, data):  # pragma: no cover
    payload = {"flash": session.pop_flash(request), "model": session.model(request)}
    payload.update(data)
    return payload


def _login_redirect_url(request):
    return request.route_url("activity.user_search", username=request.user.username)


@view_config(
    context=BadCSRFToken,
    accept="text/html",
    renderer="h:templates/accounts/session_invalid.html.jinja2",
    path_info=not_("/api"),
)
def bad_csrf_token_html(_context, request):
    request.response.status_code = 403

    next_path = "/"
    referer = urlparse(request.referer or "")
    if referer.hostname == request.domain:
        next_path = referer.path

    login_path = request.route_path("login", _query={"next": next_path})
    return {"login_path": login_path}


@json_view(context=BadCSRFToken)
def bad_csrf_token_json(_context, request):  # pragma: no cover
    request.response.status_code = 403
    reason = _("Session is invalid. Please try again.")
    return {"status": "failure", "reason": reason, "model": session.model(request)}


@json_view(context=accounts.JSONError)
def error_json(error, request):  # pragma: no cover
    request.response.status_code = 400
    return {"status": "failure", "reason": str(error)}


@json_view(context=deform.ValidationFailure)
def error_validation(error, request):  # pragma: no cover
    request.response.status_code = 400
    return ajax_payload(request, {"status": "failure", "errors": error.error.asdict()})


@view_defaults(route_name="login", renderer="h:templates/accounts/login.html.jinja2")
class AuthController:
    def __init__(self, request):
        self.request = request
        self.schema = LoginSchema().bind(request=self.request)

        # This form is used only for incoming data validation.
        self.form = request.create_form(self.schema)

        self.logout_redirect = self.request.route_url("index")

    @view_config(request_method="GET")
    @view_config(
        request_method="GET",
        request_param="for_oauth",
        renderer="h:templates/accounts/login_oauth.html.jinja2",
    )
    def get(self):
        self._redirect_if_logged_in()

        return {
            "js_config": self._js_config(),
        }

    def _js_config(self) -> dict[str, Any]:
        csrf_token = get_csrf_token(self.request)

        flash_messages: list[dict] = []
        for queue in ["success", "error"]:
            flash_messages.extend(
                {"type": queue, "message": msg}
                for msg in self.request.session.pop_flash(queue)
            )

        js_config = {
            "styles": self.request.registry["assets_env"].urls("forms_css"),
            "csrfToken": csrf_token,
            "features": {
                "log_in_with_orcid": self.request.feature("log_in_with_orcid"),
                "log_in_with_google": self.request.feature("log_in_with_google"),
                "log_in_with_facebook": self.request.feature("log_in_with_facebook"),
            },
            "flashMessages": flash_messages,
            # Prefill username from query params. This supports a flow where
            # the user is redirected to the login form with the username
            # pre-filled after activating their account.
            "form": {
                "data": {
                    "username": self.request.GET.get("username"),
                },
            },
        }

        inject_login_urls(self.request, js_config)

        if for_oauth := self.request.params.get("for_oauth"):
            js_config["forOAuth"] = bool(for_oauth)

        return js_config

    @view_config(request_method="POST")
    @view_config(
        request_method="POST",
        request_param="for_oauth",
        renderer="h:templates/accounts/login_oauth.html.jinja2",
    )
    def post(self):
        """Log the user in and redirect them."""
        self._redirect_if_logged_in()

        try:
            appstruct = self.form.validate(self.request.POST.items())
        except deform.ValidationFailure as e:
            js_config = self._js_config()
            js_config["form"] = {
                "errors": e.error.asdict(),
                "data": {
                    "username": self.request.POST.get("username", ""),
                    "password": self.request.POST.get("password", ""),
                },
            }
            return {
                "js_config": js_config,
            }

        user = appstruct["user"]
        headers = login(user, self.request)
        return httpexceptions.HTTPFound(
            location=self._login_redirect(), headers=headers
        )

    @view_config(route_name="logout", renderer=None, request_method="GET")
    def logout(self):
        """Log the user out."""
        headers = self._logout()
        return httpexceptions.HTTPFound(location=self.logout_redirect, headers=headers)

    def _redirect_if_logged_in(self):
        if self.request.authenticated_userid is not None:
            raise httpexceptions.HTTPFound(location=self._login_redirect())

    def _login_redirect(self):
        return self.request.params.get("next", _login_redirect_url(self.request))

    def _logout(self):
        if self.request.authenticated_userid is not None:
            self.request.registry.notify(LogoutEvent(self.request))
            self.request.session.invalidate()
        headers = security.forget(self.request)
        return headers


@view_defaults(
    route_name="forgot_password",
    renderer="h:templates/accounts/forgot_password.html.jinja2",
)
class ForgotPasswordController:
    """Controller for handling forgotten password forms."""

    def __init__(self, request):
        self.request = request
        self.schema = ForgotPasswordSchema().bind(request=self.request)
        self.form = request.create_form(self.schema, buttons=(_("Reset"),))

    @view_config(request_method="GET")
    def get(self):  # pragma: no cover
        """Render the forgot password page, including the form."""
        self._redirect_if_logged_in()

        return {"form": self.form.render()}

    @view_config(request_method="POST")
    def post(self):
        """
        Handle submission of the forgot password form.

        Validates that the email is one we know about, and then generates a new
        activation for the associated user, and dispatches a "reset your
        password" email which contains a token and/or link to the reset
        password form.
        """
        self._redirect_if_logged_in()

        try:
            appstruct = self.form.validate(self.request.POST.items())
        except deform.ValidationFailure:
            return {"form": self.form.render()}

        user = appstruct["user"]
        self._send_forgot_password_email(user)

        return httpexceptions.HTTPFound(self.request.route_path("account_reset"))

    def _redirect_if_logged_in(self):
        if self.request.authenticated_userid is not None:
            raise httpexceptions.HTTPFound(self.request.route_path("index"))

    def _send_forgot_password_email(self, user):
        email_data = reset_password.generate(self.request, user)
        task_data = TaskData(
            tag=email_data.tag, sender_id=user.id, recipient_ids=[user.id]
        )
        email.send.delay(asdict(email_data), asdict(task_data))


@view_defaults(
    route_name="account_reset", renderer="h:templates/accounts/reset.html.jinja2"
)
class ResetController:
    """Controller for handling password reset forms."""

    def __init__(self, request):
        self.request = request
        self.schema = ResetPasswordSchema().bind(request=self.request)
        self.form = request.create_form(
            schema=self.schema,
            action=self.request.route_path("account_reset"),
            buttons=(_("Save"),),
        )

    @view_config(request_method="GET")
    def get(self):
        """Render the reset password form."""
        return {"form": self.form.render(), "has_code": False}

    @view_config(route_name="account_reset_with_code", request_method="GET")
    def get_with_prefilled_code(self):
        """Render the reset password form with a prefilled code."""
        code = self.request.matchdict["code"]

        # If valid, we inject the supplied it into the form as a hidden field.
        # Otherwise, we 404.
        try:
            user = ResetCode().deserialize(self.schema, code)
        except colander.Invalid as err:
            raise httpexceptions.HTTPNotFound() from err  # noqa: RSE102

        # N.B. the form field for the reset code is called 'user'. See the
        # comment in `~h.schemas.forms.accounts.ResetPasswordSchema` for details.
        self.form.set_appstruct({"user": user})
        self.form.set_widgets({"user": deform.widget.HiddenWidget()})

        return {"form": self.form.render(), "has_code": True}

    @view_config(request_method="POST")
    def post(self):
        """
        Handle submission of the reset password form.

        This function checks that the activation code (i.e. reset token)
        provided by the form is valid, retrieves the user associated with the
        activation code, and resets their password.
        """
        try:
            appstruct = self.form.validate(self.request.POST.items())
        except deform.ValidationFailure:
            # If the code is valid, hide the field.
            if not self.form["user"].error:  # pragma: no cover
                self.form.set_widgets({"user": deform.widget.HiddenWidget()})
            return {"form": self.form.render()}

        user = appstruct["user"]

        self._reset_password(user, appstruct["password"])

        return httpexceptions.HTTPFound(
            location=self.request.route_path(
                "login", _query={"username": user.username}
            )
        )

    def _redirect_if_logged_in(self):
        if self.request.authenticated_userid is not None:  # pragma: no cover
            raise httpexceptions.HTTPFound(self.request.route_path("index"))

    def _reset_password(self, user, password):
        svc = self.request.find_service(name="user_password")
        svc.update_password(user, password)

        self.request.session.flash(
            Markup(
                _(
                    "Your password has been reset. You can now log in with "
                    "your new password."
                )
            ),
            "success",
        )
        self.request.registry.notify(PasswordResetEvent(self.request, user))


@view_defaults(route_name="activate")
class ActivateController:
    def __init__(self, request):
        self.request = request

    @view_config(request_method="GET")
    def get_when_not_logged_in(self):
        """
        Handle a request for a user activation link.

        Checks if the activation code passed is valid, and (as a safety check)
        that it is an activation for the passed user id. If all is well,
        activate the user and redirect them.
        """
        code = self.request.matchdict.get("code")
        id_ = self.request.matchdict.get("id")

        try:
            id_ = int(id_)
        except ValueError as err:
            raise httpexceptions.HTTPNotFound() from err  # noqa: RSE102

        activation = models.Activation.get_by_code(self.request.db, code)
        if activation is None:
            self.request.session.flash(
                Markup(
                    _(
                        "We didn't recognize that activation link. "
                        "Have you already activated your account? "
                        "If so, try logging in using the username "
                        "and password that you provided."
                    ),
                ),
                "error",
            )
            return httpexceptions.HTTPFound(location=self.request.route_url("login"))

        user = models.User.get_by_activation(self.request.db, activation)
        if user is None or user.id != id_:
            raise httpexceptions.HTTPNotFound()  # noqa: RSE102

        user.activate()

        self.request.session.flash(
            Markup(
                _(
                    "Your account has been activated! "
                    "You can now log in using the password you provided."
                ),
            ),
            "success",
        )

        self.request.registry.notify(ActivationEvent(self.request, user))

        return httpexceptions.HTTPFound(
            location=self.request.route_url("login", _query={"username": user.username})
        )

    @view_config(request_method="GET", is_authenticated=True)
    def get_when_logged_in(self):
        """Handle an activation link request while already logged in."""
        id_ = self.request.matchdict.get("id")

        try:
            id_ = int(id_)
        except ValueError as err:
            raise httpexceptions.HTTPNotFound() from err  # noqa: RSE102

        if id_ == self.request.user.id:
            # The user is already logged in to the account (so the account
            # must already be activated).
            self.request.session.flash(
                Markup(_("Your account has been activated and you're logged in.")),
                "success",
            )
        else:
            self.request.session.flash(
                Markup(
                    _(
                        "You're already logged in to a different account. "
                        '<a href="{url}">Log out</a> and open the activation link '
                        "again."
                    ).format(url=self.request.route_url("logout"))
                ),
                "error",
            )

        return httpexceptions.HTTPFound(location=self.request.route_url("index"))


@view_defaults(
    route_name="account",
    renderer="h:templates/accounts/account.html.jinja2",
    is_authenticated=True,
)
class AccountController:
    def __init__(self, context, request):
        self.context = context
        self.request = request

    @view_config(request_method="GET")
    def get(self):
        return self._template_data()

    @view_config(
        request_method="POST", request_param="__formid__=email", require_csrf=True
    )
    def post_email_form(self):
        if self.request.user.password:
            schema = schemas.EmailChangeSchema()
        else:
            schema = schemas.EmailAddSchema()

        appstruct = self.request.create_form(
            schema.bind(request=self.request)
        ).validate(self.request.POST.items())

        self.request.user.email = appstruct["email"]

        self.request.session.flash("Email address changed ✓", "success")
        return httpexceptions.HTTPFound(location=self.request.route_url("account"))

    @view_config(
        request_method="POST", request_param="__formid__=password", require_csrf=True
    )
    def post_password_form(self):
        if self.request.user.password:
            schema = schemas.PasswordChangeSchema()
        else:
            schema = schemas.PasswordAddSchema()

        appstruct = self.request.create_form(
            schema.bind(request=self.request)
        ).validate(self.request.POST.items())

        self.request.find_service(name="user_password").update_password(
            self.request.user, appstruct["new_password"]
        )

        self.request.session.flash("Password changed ✓", "success")
        return httpexceptions.HTTPFound(location=self.request.route_url("account"))

    @exception_view_config(
        context=deform.ValidationFailure, request_param="__formid__=email"
    )
    @exception_view_config(
        context=deform.ValidationFailure, request_param="__formid__=password"
    )
    def validation_failure(self):
        self.request.response.status_int = 400

        formid = self.request.params["__formid__"]

        data = {}

        # Form fields that're safe to copy from the request into the response
        # (so that the form doesn't lose the text the user entered) when
        # responding with a validation error.
        # Fields containing passwords are omitted for security.
        safe_fields = ["email"]

        for field in safe_fields:
            if field in self.request.params:
                data[field] = self.request.params[field]
            else:  # pragma: nocover
                pass

        return self._template_data(
            js_config={
                "forms": {formid: {"data": data, "errors": self.context.error.asdict()}}
            }
        )

    def _template_data(self, js_config=None):
        js_config = js_config or {}
        js_config.setdefault("csrfToken", get_csrf_token(self.request))
        js_config.setdefault("forms", {})
        js_config["forms"].setdefault("email", {})
        js_config["forms"]["email"].setdefault("data", {})
        js_config["forms"]["email"].setdefault("errors", {})
        js_config["forms"].setdefault("password", {})
        js_config["forms"]["password"].setdefault("data", {})
        js_config["forms"]["password"].setdefault("errors", {})
        js_config.setdefault("features", {})
        for provider in IdentityProvider:
            js_config["features"].setdefault(
                f"log_in_with_{provider.name.lower()}",
                self.request.feature(f"log_in_with_{provider.name.lower()}"),
            )
        js_config.setdefault("context", {})
        js_config["context"].setdefault("user", {})
        js_config["context"]["user"].setdefault(
            "email", self.request.user.email or None
        )
        js_config["context"]["user"].setdefault(
            "has_password", bool(self.request.user.password)
        )

        oidc_svc = self.request.find_service(OIDCService)

        for provider in IdentityProvider:
            if js_config["features"][f"log_in_with_{provider.name.lower()}"]:
                provider_config = {}
                identity = oidc_svc.get_identity(self.request.user, provider)

                if identity:
                    provider_config["connected"] = True
                    provider_config["provider_unique_id"] = identity.provider_unique_id
                else:
                    provider_config["connected"] = False

                js_config["context"].setdefault("identities", {})
                js_config["context"]["identities"].setdefault(provider.name.lower(), {})
                for key, value in provider_config.items():
                    js_config["context"]["identities"][
                        provider.name.lower()
                    ].setdefault(key, value)

                route_name = f"oidc.connect.{provider.name.lower()}"
                js_config.setdefault("routes", {})
                js_config["routes"].setdefault(
                    route_name, self.request.route_url(route_name)
                )

        js_config.setdefault("routes", {})["identity_delete"] = self.request.route_url(
            "account_identity"
        )

        orcid_config = js_config["context"].get("identities", {}).get("orcid", {})
        if orcid_id := orcid_config.get("provider_unique_id"):
            orcid_host = self.request.registry.settings["orcid_host"]
            # The URL to the user's public ORCID profile page
            # (for example: https://orcid.org/0000-0002-6373-1308).
            orcid_config.setdefault(
                "url", urlunparse(urlparse(orcid_host)._replace(path=orcid_id))
            )

        return {"js_config": js_config}


@view_config(
    route_name="account_identity",
    is_authenticated=True,
    request_method="POST",
    require_csrf=True,
    request_param=("provider", "provider_unique_id"),
)
def delete_identity(request):
    user = request.user
    db = request.db
    flash = request.session.flash
    params = request.params
    route_url = request.route_url

    try:
        given_provider = IdentityProvider[params["provider"].upper()]
    except KeyError as err:
        raise httpexceptions.HTTPNotFound from err

    given_provider_unique_id = params["provider_unique_id"]

    identities = db.scalars(select(UserIdentity).where(UserIdentity.user_id == user.id))

    matching_identity = None
    other_identities = []
    for identity in identities:
        if (
            identity.provider == given_provider
            and identity.provider_unique_id == given_provider_unique_id
        ):
            assert matching_identity is None  # noqa:S101
            matching_identity = identity
        else:
            other_identities.append(identity)

    if not matching_identity:
        flash(
            _(
                "{provider} not connected. Did you already disconnect this provider in another tab?"
            ).format(provider=given_provider),
            "error",
        )
    elif any((user.password, other_identities)):
        db.delete(matching_identity)
        flash(
            _("{provider} disconnected ✓").format(provider=matching_identity.provider),
            "success",
        )
    else:
        flash(
            _(
                "Can't disconnect account:"
                " {provider} is currently the only way to log in to your Hypothesis account."
                " Connect another account or add a password first."
            ).format(provider=matching_identity.provider),
            "error",
        )

    return httpexceptions.HTTPFound(location=route_url("account"))


@view_defaults(
    route_name="account_profile",
    renderer="h:templates/accounts/profile.html.jinja2",
    is_authenticated=True,
)
class EditProfileController:
    def __init__(self, request):
        self.request = request
        self.schema = EditProfileSchema().bind(request=self.request)
        self.form = request.create_form(self.schema)

    @view_config(request_method="GET")
    def get(self):
        """Render the 'Edit Profile' form."""
        return self._template_data()

    @view_config(request_method="POST")
    def post(self):
        return form.handle_form_submission(
            self.request,
            self.form,
            on_success=self._update_user,
            on_failure=self._template_data,
        )

    def _template_data(self, errors=None, items=None):
        if errors is None:
            errors = {}
        if items is None:
            items = {}

        user = self.request.user
        form_data = {
            "display_name": items.get("display_name", user.display_name or ""),
            "description": items.get("description", user.description or ""),
            "location": items.get("location", user.location or ""),
            "link": items.get("link", user.uri or ""),
            "orcid": items.get("orcid", user.orcid or ""),
        }

        return {
            "js_config": {
                "csrfToken": get_csrf_token(self.request),
                "features": {},
                "form": {
                    "data": form_data,
                    "errors": errors,
                },
            }
        }

    def _update_user(self, appstruct):
        user = self.request.user
        user.display_name = appstruct["display_name"]
        user.description = appstruct["description"]
        user.location = appstruct["location"]
        user.uri = appstruct["link"]
        user.orcid = appstruct["orcid"]


@view_defaults(
    route_name="account_notifications",
    renderer="h:templates/accounts/notifications.html.jinja2",
    is_authenticated=True,
)
class NotificationsController:
    def __init__(self, request) -> None:
        self.request = request
        self.schema = schemas.NotificationsSchema().bind(request=self.request)
        self.subscription_svc: SubscriptionService = request.find_service(
            SubscriptionService
        )
        self.form = request.create_form(
            self.schema, buttons=(_("Save"),), use_inline_editing=True
        )

    @view_config(request_method="GET")
    def get(self):
        """Render the notifications form."""
        active_subscriptions = {
            subscription.type
            for subscription in self.subscription_svc.get_all_subscriptions(
                user_id=self.request.authenticated_userid
            )
            if subscription.active
        }

        self.form.set_appstruct({"notifications": active_subscriptions})
        return self._template_data()

    @view_config(request_method="POST")
    def post(self):
        """Process notifications POST data."""
        return form.handle_form_submission(
            self.request,
            self.form,
            on_success=self._update_notifications,
            on_failure=self._template_data,
        )

    def _update_notifications(self, appstruct):
        active_subscriptions = set(appstruct["notifications"])
        for subscription in self.subscription_svc.get_all_subscriptions(
            user_id=self.request.authenticated_userid
        ):
            subscription.active = subscription.type in active_subscriptions

    def _template_data(self, errors=None, items=None):
        if errors is None:
            errors = {}
        if items is None:
            items = {}

        user_has_email_address = self.request.user and self.request.user.email
        data = {"user_has_email_address": user_has_email_address}

        if user_has_email_address:
            data["form"] = self.form.render()

        return data


@view_defaults(
    route_name="account_developer",
    renderer="h:templates/accounts/developer.html.jinja2",
    is_authenticated=True,
)
class DeveloperController:
    def __init__(self, request):
        self.request = request
        self.svc = request.find_service(name="developer_token")

        self.userid = request.authenticated_userid

    @view_config(request_method="GET")
    def get(self):
        """Render the developer page, including the form."""
        token = self.svc.fetch(self.userid)

        if token:
            return {"token": token.value}

        return {}

    @view_config(request_method="POST")
    def post(self):
        """(Re-)generate the user's API token."""
        token = self.svc.fetch(self.userid)

        if token:  # noqa: SIM108
            # The user already has an API token, regenerate it.
            token = self.svc.regenerate(token)
        else:
            # The user doesn't have an API token yet, generate one for them.
            token = self.svc.create(self.userid)

        return {"token": token.value}


@view_defaults(
    route_name="account_delete",
    renderer="h:templates/accounts/delete.html.jinja2",
    is_authenticated=True,
)
class DeleteController:
    def __init__(self, request):
        self.request = request

        schema = schemas.DeleteAccountSchema().bind(request=self.request)

        self.form = self.request.create_form(
            schema,
            buttons=(deform.Button(_("Delete your account"), css_class="btn--danger"),),
            formid="delete",
            back_link={
                "href": self.request.route_url("account"),
                "text": _("Back to safety"),
            },
        )

    @view_config(request_method="GET")
    def get(self):
        return self.template_data()

    @view_config(request_method="POST")
    def post(self):
        return form.handle_form_submission(
            self.request,
            self.form,
            on_success=self.delete_user,
            on_failure=self.template_data,
            flash_success=False,
        )

    def delete_user(self, _appstruct):
        self.request.find_service(name="user_delete").delete_user(
            self.request.user,
            requested_by=self.request.user,
            tag=self.request.matched_route.name,
        )

        return httpexceptions.HTTPFound(
            location=self.request.route_url("account_deleted")
        )

    def template_data(self):
        def query(column):
            return (
                select(column)
                .where(Annotation.deleted.is_(False))
                .where(Annotation.userid == self.request.authenticated_userid)
            )

        count = self.request.db.scalar(query(func.count(Annotation.id)))

        oldest = self.request.db.scalar(
            query(Annotation.created).order_by(Annotation.created)
        )

        newest = self.request.db.scalar(
            query(Annotation.created).order_by(Annotation.created.desc())
        )

        return {
            "count": count,
            "oldest": oldest,
            "newest": newest,
            "form": self.form.render(),
        }


# TODO: This can be removed after October 2016, which will be >1 year from the  # noqa: FIX002, TD002, TD003
#       date that the last account claim emails were sent out. At this point,
#       if we have not done so already, we should remove all unclaimed
#       usernames from the accounts tables.
@view_config(
    route_name="claim_account_legacy",
    request_method="GET",
    renderer="h:templates/accounts/claim_account_legacy.html.jinja2",
)
def claim_account_legacy(_request):  # pragma: no cover
    """Render a page explaining that claim links are no longer valid."""
    return {}


@view_config(
    route_name="dismiss_sidebar_tutorial", request_method="POST", renderer="json"
)
def dismiss_sidebar_tutorial(request):  # pragma: no cover
    if request.authenticated_userid is None:
        raise accounts.JSONError()  # noqa: RSE102

    request.user.sidebar_tutorial_dismissed = True
    return ajax_payload(request, {"status": "okay"})


@view_config(
    route_name="account_deleted",
    request_method="GET",
    renderer="h:templates/accounts/deleted.html.jinja2",
)
def account_deleted(_request):
    return {}
