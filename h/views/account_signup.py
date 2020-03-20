# -*- coding: utf-8 -*-

import datetime

import deform
from pyramid import httpexceptions
from pyramid.view import view_config, view_defaults

from h import i18n
from h.accounts import schemas
from h.services.exceptions import ConflictError

_ = i18n.TranslationString


def _login_redirect_url(request):
    return request.route_url("activity.user_search", username=request.user.username)


@view_defaults(route_name="signup")
class SignupController:
    def __init__(self, request):

        self.request = request
        self.schema = schemas.RegisterSchema().bind(request=self.request)
        self.form = request.create_form(
            self.schema,
            buttons=(deform.Button(title=_("Sign up")),),
            css_class="js-disable-on-submit",
        )

    @view_config(
        request_method="GET", renderer="h:templates/accounts/signup.html.jinja2"
    )
    def get(self):
        """Render the empty registration form."""
        self._redirect_if_logged_in()

        return {"form": self.form.render()}

    @view_config(
        request_method="POST",
        renderer="h:templates/accounts/signup-successful.html.jinja2",
    )
    def post(self):
        """Handle submission of the new user registration form."""
        self._redirect_if_logged_in()

        try:
            appstruct = self.form.validate(self.request.POST.items())
        except deform.ValidationFailure:
            return {"form": self.form.render()}

        signup_service = self.request.find_service(name="user_signup")

        template_context = {"heading": _("Account registration successful")}
        try:
            signup_service.signup(
                username=appstruct["username"],
                email=appstruct["email"],
                password=appstruct["password"],
                privacy_accepted=datetime.datetime.utcnow(),
            )
        except ConflictError as e:
            template_context["heading"] = _("Account already registered")
            template_context["message"] = _(
                "{failure_reason}".format(failure_reason=e.args[0])
            )

        return template_context

    def _redirect_if_logged_in(self):
        if self.request.authenticated_userid is not None:
            raise httpexceptions.HTTPFound(_login_redirect_url(self.request))
