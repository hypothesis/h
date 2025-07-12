import datetime
from typing import Any

from deform import ValidationFailure
from h_pyramid_sentry import report_exception
from jwt import InvalidTokenError
from pyramid.csrf import get_csrf_token
from pyramid.httpexceptions import HTTPFound
from pyramid.view import exception_view_config, view_config, view_defaults

from h import i18n
from h.accounts.schemas import ORCIDSignupSchema, SignupSchema
from h.models.user_identity import IdentityProvider
from h.services.exceptions import ConflictError
from h.views.helpers import login

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
        feature_service = self.request.find_service(name="feature")

        return {
            "csrfToken": get_csrf_token(self.request),
            "features": {
                "log_in_with_orcid": feature_service.enabled(
                    "log_in_with_orcid", user=None
                )
            },
        }


class AuthJWTDecodeError(Exception):
    """Decoding the `auth` JWT query param failed."""


class InvalidAuthJWTPayloadError(Exception):
    """The `auth` JWT query param decoded to an unexpected payload."""


@view_defaults(
    route_name="signup.orcid",
    is_authenticated=False,
    request_param="auth",
    renderer="h:templates/accounts/signup.html.jinja2",
)
class ORCIDSignupViews:
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.jwt_service = request.find_service(name="jwt")

    @view_config(request_method="GET")
    def get(self):
        self.orcid_id = self.decode_orcid_id()

        return {"js_config": self.js_config}

    @view_config(request_method="POST")
    def post(self):
        self.orcid_id = self.decode_orcid_id()

        form = self.request.create_form(ORCIDSignupSchema().bind(request=self.request))

        appstruct = form.validate(self.request.POST.items())

        signup_service = self.request.find_service(name="user_signup")

        user = signup_service.signup(
            username=appstruct["username"],
            email=None,
            password=None,
            privacy_accepted=datetime.datetime.now(datetime.UTC),
            comms_opt_in=bool(appstruct.get("comms_opt_in", False)),
            require_activation=False,
            identities=[
                {
                    "provider": IdentityProvider.ORCID,
                    "provider_unique_id": self.orcid_id,
                }
            ],
        )

        return HTTPFound(
            self.request.route_url("activity.user_search", username=user.username),
            headers=login(user, self.request),
        )

    @exception_view_config(
        context=AuthJWTDecodeError, renderer="h:templates/error.html.jinja2"
    )
    def auth_jwt_decode_error(self):
        report_exception(self.context)
        self.request.response.status_int = 403
        return {"error": "Decoding auth JWT failed."}

    @exception_view_config(context=ValidationFailure)
    def validation_failure(self):
        self.orcid_id = self.decode_orcid_id()
        self.request.response.status_int = 400

        return {
            "js_config": {
                "formErrors": self.context.error.asdict(),
                "formData": {
                    "username": self.request.POST.get("username", ""),
                    "privacy_accepted": self.request.POST.get("privacy_accepted", "")
                    == "true",
                    "comms_opt_in": self.request.POST.get("comms_opt_in", "") == "true",
                    # When reloading the page replace the auth token with a fresh one.
                    "auth": self.encode_idinfo(self.jwt_service, self.orcid_id),
                },
                **self.js_config,
            }
        }

    @property
    def js_config(self):
        feature_service = self.request.find_service(name="feature")

        return {
            "csrfToken": get_csrf_token(self.request),
            "features": {
                "log_in_with_orcid": feature_service.enabled(
                    "log_in_with_orcid", user=None
                )
            },
            "identity": {"orcid": {"id": self.orcid_id}},
        }

    def decode_orcid_id(self):
        try:
            idinfo = self.jwt_service.decode_idinfo(
                "orcid", self.request.params["auth"]
            )
        except InvalidTokenError as err:
            raise AuthJWTDecodeError from err

        try:
            orcid_id = idinfo["id"]
        except (KeyError, TypeError) as err:
            raise InvalidAuthJWTPayloadError from err

        if not isinstance(orcid_id, str):
            raise InvalidAuthJWTPayloadError

        if orcid_id == "":
            raise InvalidAuthJWTPayloadError

        return orcid_id

    @staticmethod
    def encode_idinfo(jwt_service, orcid_id):
        return jwt_service.encode_idinfo("orcid", {"id": orcid_id})


# It's possible to try to sign up while already logged in. For example: start
# to signup but don't submit the final form, then open a new tab and log in,
# then return to the first tab and submit the signup form. This view is called
# in these cases.
@view_config(route_name="signup", is_authenticated=True)
@view_config(route_name="signup.orcid", is_authenticated=True)
def is_authenticated(request):
    request.session.flash(_("You're already logged in."), "error")
    return HTTPFound(
        request.route_url("activity.user_search", username=request.user.username)
    )
