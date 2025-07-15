import datetime
from typing import Any

from deform import ValidationFailure
from pyramid.csrf import get_csrf_token
from pyramid.httpexceptions import HTTPFound
from pyramid.view import exception_view_config, view_config, view_defaults

from h import i18n
from h.accounts.schemas import SignupSchema
from h.services.exceptions import ConflictError

_ = i18n.TranslationString


@view_defaults(route_name="signup", is_authenticated=False)
class SignupViews:
    def __init__(self, context, request):
        self.context = context
        self.request = request

    @view_config(
        request_method="GET", renderer="h:templates/accounts/signup.html.jinja2"
    )
    def get(self):
        """Render the empty registration form."""
        return {"js_config": self.js_config}

    @view_config(
        request_method="POST", renderer="h:templates/accounts/signup-post.html.jinja2"
    )
    def post(self):
        """Handle submission of the new user registration form."""
        form = self.request.create_form(SignupSchema().bind(request=self.request))

        appstruct = form.validate(self.request.POST.items())

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

    @exception_view_config(
        ValidationFailure,
        request_method="POST",
        renderer="h:templates/accounts/signup-post.html.jinja2",
    )
    def validation_failure(self):
        return {
            "js_config": {
                "formErrors": self.context.error.asdict(),
                "formData": {
                    "username": self.request.POST.get("username", ""),
                    "email": self.request.POST.get("email", ""),
                    "password": self.request.POST.get("password", ""),
                    "privacy_accepted": self.request.POST.get("privacy_accepted", "")
                    == "true",
                    "comms_opt_in": self.request.POST.get("comms_opt_in", "") == "true",
                },
                **self.js_config,
            }
        }

    @property
    def js_config(self) -> dict[str, Any]:
        return {"csrfToken": get_csrf_token(self.request)}


# It's possible to try to sign up while already logged in. For example: start
# to signup but don't submit the final form, then open a new tab and log in,
# then return to the first tab and submit the signup form. This view is called
# in these cases.
@view_config(route_name="signup", is_authenticated=True)
def is_authenticated(request):
    return HTTPFound(
        request.route_url("activity.user_search", username=request.user.username)
    )
