import datetime
import itertools
from urllib.parse import urlparse

import colander
import deform
import jinja2
from pyramid import httpexceptions, security
from pyramid.exceptions import BadCSRFToken
from pyramid.view import view_config, view_defaults

from h import accounts, form, i18n, models, session
from h.accounts import schemas
from h.accounts.events import (
    ActivationEvent,
    LoginEvent,
    LogoutEvent,
    PasswordResetEvent,
)
from h.emails import reset_password
from h.schemas.forms.accounts import (
    EditProfileSchema,
    ForgotPasswordSchema,
    LoginSchema,
    ResetCode,
    ResetPasswordSchema,
)
from h.services import SubscriptionService
from h.tasks import mailer
from h.util.view import json_view

_ = i18n.TranslationString


# A little helper to ensure that session data is returned in every ajax
# response payload.
def ajax_payload(request, data):
    payload = {"flash": session.pop_flash(request), "model": session.model(request)}
    payload.update(data)
    return payload


def _login_redirect_url(request):
    return request.route_url("activity.user_search", username=request.user.username)


@view_config(
    context=BadCSRFToken,
    accept="text/html",
    renderer="h:templates/accounts/session_invalid.html.jinja2",
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
def bad_csrf_token_json(_context, request):
    request.response.status_code = 403
    reason = _("Session is invalid. Please try again.")
    return {"status": "failure", "reason": reason, "model": session.model(request)}


@json_view(context=accounts.JSONError)
def error_json(error, request):
    request.response.status_code = 400
    return {"status": "failure", "reason": str(error)}


@json_view(context=deform.ValidationFailure)
def error_validation(error, request):
    request.response.status_code = 400
    return ajax_payload(request, {"status": "failure", "errors": error.error.asdict()})


@view_defaults(route_name="login", renderer="h:templates/accounts/login.html.jinja2")
class AuthController:
    def __init__(self, request):
        form_footer = '<a class="link" href="{href}">{text}</a>'.format(  # pylint: disable=consider-using-f-string
            href=request.route_path("forgot_password"), text=_("Forgot your password?")
        )

        self.request = request
        self.schema = LoginSchema().bind(request=self.request)

        show_cancel_button = bool(request.params.get("for_oauth", False))
        self.form = request.create_form(
            self.schema,
            buttons=(_("Log in"),),
            footer=form_footer,
            show_cancel_button=show_cancel_button,
        )

        self.logout_redirect = self.request.route_url("index")

    @view_config(request_method="GET")
    @view_config(
        request_method="GET",
        request_param="for_oauth",
        renderer="h:templates/accounts/login_oauth.html.jinja2",
    )
    def get(self):
        """Render the login page, including the login form."""
        self._redirect_if_logged_in()

        return {"form": self.form.render(LoginSchema.default_values(self.request))}

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
        except deform.ValidationFailure:
            return {"form": self.form.render()}

        user = appstruct["user"]
        headers = self._login(user)
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

    def _login(self, user):
        user.last_login_date = datetime.datetime.utcnow()
        self.request.registry.notify(LoginEvent(self.request, user))
        headers = security.remember(self.request, user.userid)
        return headers

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
    def get(self):
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
        send_params = reset_password.generate(self.request, user)
        mailer.send.delay(*send_params)


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
            raise httpexceptions.HTTPNotFound() from err
        else:
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
            if not self.form["user"].error:
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
        if self.request.authenticated_userid is not None:
            raise httpexceptions.HTTPFound(self.request.route_path("index"))

    def _reset_password(self, user, password):
        svc = self.request.find_service(name="user_password")
        svc.update_password(user, password)

        self.request.session.flash(
            jinja2.Markup(
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
            raise httpexceptions.HTTPNotFound() from err

        activation = models.Activation.get_by_code(self.request.db, code)
        if activation is None:
            self.request.session.flash(
                jinja2.Markup(
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
            raise httpexceptions.HTTPNotFound()

        user.activate()

        self.request.session.flash(
            jinja2.Markup(
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
            raise httpexceptions.HTTPNotFound() from err

        if id_ == self.request.user.id:
            # The user is already logged in to the account (so the account
            # must already be activated).
            self.request.session.flash(
                jinja2.Markup(
                    _("Your account has been activated and you're logged in.")
                ),
                "success",
            )
        else:
            self.request.session.flash(
                jinja2.Markup(
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
    def __init__(self, request):
        self.request = request

        email_schema = schemas.EmailChangeSchema().bind(request=request)
        password_schema = schemas.PasswordChangeSchema().bind(request=request)

        # Ensure deform generates unique field IDs for each field in this
        # multiple-form page.
        counter = itertools.count()

        self.forms = {
            "email": request.create_form(
                email_schema,
                buttons=(_("Save"),),
                formid="email",
                counter=counter,
                use_inline_editing=True,
            ),
            "password": request.create_form(
                password_schema,
                buttons=(_("Save"),),
                formid="password",
                counter=counter,
                use_inline_editing=True,
            ),
        }

    @view_config(request_method="GET")
    def get(self):
        """Show the user's account."""
        return self._template_data()

    @view_config(request_method="POST", request_param="__formid__=email")
    def post_email_form(self):
        # Called by Pyramid when the change email form is submitted.
        return form.handle_form_submission(
            self.request,
            self.forms["email"],
            on_success=self.update_email_address,
            on_failure=self._template_data,
        )

    @view_config(request_method="POST", request_param="__formid__=password")
    def post_password_form(self):
        # Called by Pyramid when the change password form is submitted.
        return form.handle_form_submission(
            self.request,
            self.forms["password"],
            on_success=self.update_password,
            on_failure=self._template_data,
        )

    def update_email_address(self, appstruct):
        self.request.user.email = appstruct["email"]

    def update_password(self, appstruct):
        svc = self.request.find_service(name="user_password")
        svc.update_password(self.request.user, appstruct["new_password"])

    def _template_data(self):
        """Return the data needed to render accounts.html.jinja2."""
        email = self.request.user.email or ""
        password_form = self.forms["password"].render()
        email_form = self.forms["email"].render({"email": email})

        return {
            "email": email,
            "email_form": email_form,
            "password_form": password_form,
        }


@view_defaults(
    route_name="account_profile",
    renderer="h:templates/accounts/profile.html.jinja2",
    is_authenticated=True,
)
class EditProfileController:
    def __init__(self, request):
        self.request = request
        self.schema = EditProfileSchema().bind(request=self.request)
        self.form = request.create_form(
            self.schema, buttons=(_("Save"),), use_inline_editing=True
        )

    @view_config(request_method="GET")
    def get(self):
        """Render the 'Edit Profile' form."""
        user = self.request.user
        self.form.set_appstruct(
            {
                "display_name": user.display_name or "",
                "description": user.description or "",
                "location": user.location or "",
                "link": user.uri or "",
                "orcid": user.orcid or "",
            }
        )
        return self._template_data()

    @view_config(request_method="POST")
    def post(self):
        return form.handle_form_submission(
            self.request,
            self.form,
            on_success=self._update_user,
            on_failure=self._template_data,
        )

    def _template_data(self):
        return {"form": self.form.render()}

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
    def __init__(self, request):
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

    def _template_data(self):
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

        if token:
            # The user already has an API token, regenerate it.
            token = self.svc.regenerate(token)
        else:
            # The user doesn't have an API token yet, generate one for them.
            token = self.svc.create(self.userid)

        return {"token": token.value}


# TODO: This can be removed after October 2016, which will be >1 year from the
#       date that the last account claim emails were sent out. At this point,
#       if we have not done so already, we should remove all unclaimed
#       usernames from the accounts tables.
@view_config(
    route_name="claim_account_legacy",
    request_method="GET",
    renderer="h:templates/accounts/claim_account_legacy.html.jinja2",
)
def claim_account_legacy(_request):
    """Render a page explaining that claim links are no longer valid."""
    return {}


@view_config(
    route_name="dismiss_sidebar_tutorial", request_method="POST", renderer="json"
)
def dismiss_sidebar_tutorial(request):
    if request.authenticated_userid is None:
        raise accounts.JSONError()

    request.user.sidebar_tutorial_dismissed = True
    return ajax_payload(request, {"status": "okay"})
