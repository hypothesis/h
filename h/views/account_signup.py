import datetime
from typing import Any

from deform import ValidationFailure
from pyramid import httpexceptions
from pyramid.csrf import get_csrf_token
from pyramid.view import view_config, view_defaults

from h import i18n
from h.accounts.schemas import RegisterSchema
from h.services.exceptions import ConflictError

_ = i18n.TranslationString


@view_defaults(route_name="signup")
class SignupViews:
    def __init__(self, request):
        self.request = request

    @view_config(
        request_method="GET", renderer="h:templates/accounts/signup.html.jinja2"
    )
    def get(self):
        """Render the empty registration form."""
        self.redirect_if_logged_in()

        return {"js_config": self.js_config}

    @view_config(
        request_method="POST", renderer="h:templates/accounts/signup-post.html.jinja2"
    )
    def post(self):
        """Handle submission of the new user registration form."""
        self.redirect_if_logged_in()

        form = self.request.create_form(RegisterSchema().bind(request=self.request))

        try:
            appstruct = form.validate(self.request.POST.items())
        except ValidationFailure as e:
            js_config = self.js_config
            js_config["formErrors"] = e.error.asdict()
            js_config["formData"] = {
                "username": self.request.POST.get("username", ""),
                "email": self.request.POST.get("email", ""),
                "password": self.request.POST.get("password", ""),
                "privacy_accepted": self.request.POST.get("privacy_accepted", "")
                == "true",
                "comms_opt_in": self.request.POST.get("comms_opt_in", "") == "true",
            }
            return {"js_config": js_config}

        signup_service = self.request.find_service(name="user_signup")

        heading = _("Account registration successful")
        message = None
        try:
            signup_service.signup(
                username=appstruct["username"],
                email=appstruct["email"],
                password=appstruct["password"],
                privacy_accepted=datetime.datetime.now(datetime.UTC),
                comms_opt_in=appstruct["comms_opt_in"],
            )
        except ConflictError as exc:
            heading = _("Account already registered")
            message = _(f"{exc.args[0]}")  # noqa: INT001

        return {"js_config": self.js_config, "heading": heading, "message": message}

    @property
    def js_config(self) -> dict[str, Any]:
        return {"csrfToken": get_csrf_token(self.request)}

    def redirect_if_logged_in(self):
        if self.request.authenticated_userid is not None:
            raise httpexceptions.HTTPFound(
                self.request.route_url(
                    "activity.user_search", username=self.request.user.username
                )
            )
