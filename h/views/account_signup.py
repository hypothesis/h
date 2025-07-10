import datetime
from dataclasses import dataclass
from typing import Any

import jwt
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
from h.views.oidc import JWT_SIGNING_ALGORITHM

_ = i18n.TranslationString


@view_defaults(route_name="signup")
class SignupViews:
    def __init__(self, context, request):
        self.context = context
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

    def redirect_if_logged_in(self):
        if self.request.authenticated_userid is not None:
            raise HTTPFound(
                self.request.route_url(
                    "activity.user_search", username=self.request.user.username
                )
            )


class AuthJWTDecodeError(Exception):
    """Decoding the `auth` JWT query param failed."""


class InvalidAuthJWTPayloadError(Exception):
    """The `auth` JWT query param decoded to an unexpected payload."""


@dataclass
class AuthJWTPayload:
    orcid_id: str


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

    @view_config(request_method="GET")
    def get(self):
        # Do this first so that if decoding the auth JWT fails we fail right
        # away, before the view potentially does anything else.
        auth = self.decode_authjwt()

        return {"js_config": self.js_config(auth)}

    @view_config(request_method="POST")
    def post(self):
        # Do this first so that if decoding the auth JWT fails we fail right
        # away, before the view potentially does anything else.
        auth = self.decode_authjwt()

        form = self.request.create_form(ORCIDSignupSchema().bind(request=self.request))

        appstruct = form.validate(self.request.POST.items())

        signup_service = self.request.find_service(name="user_signup")

        user = signup_service.signup(
            username=appstruct["username"],
            email=None,
            password=None,
            privacy_accepted=datetime.datetime.now(datetime.UTC),
            comms_opt_in=appstruct.get("comms_opt_in", None) == "yes",
            require_activation=False,
            identities=[
                {
                    "provider": IdentityProvider.ORCID,
                    "provider_unique_id": auth.orcid_id,
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
    def form_validation_error(self):
        self.request.response.status_int = 400
        return {
            "js_config": {
                "formErrors": self.context.error.asdict(),
                "formData": {
                    "username": self.request.POST.get("username", ""),
                    "privacy_accepted": self.request.POST.get("privacy_accepted", "")
                    == "true",
                    "comms_opt_in": self.request.POST.get("comms_opt_in", "") == "true",
                },
                **self.js_config(self.decode_authjwt()),
            }
        }

    def js_config(self, auth):
        return {
            "csrfToken": get_csrf_token(self.request),
            "identity": {str(IdentityProvider.ORCID): {"id": auth.orcid_id}},
        }

    def decode_authjwt(self) -> AuthJWTPayload:
        authjwt = self.request.params["auth"]
        authjwt_signing_key = self.request.registry.settings[
            "orcid_oidc_authjwt_signing_key"
        ]

        try:
            decoded_auth_jwt = jwt.decode(
                authjwt, authjwt_signing_key, algorithms=[JWT_SIGNING_ALGORITHM]
            )
        except InvalidTokenError as err:
            raise AuthJWTDecodeError from err

        try:
            orcid_id = decoded_auth_jwt["identity"][str(IdentityProvider.ORCID)]["id"]
        except (KeyError, TypeError) as err:
            raise InvalidAuthJWTPayloadError from err

        if not isinstance(orcid_id, str):
            raise InvalidAuthJWTPayloadError

        if orcid_id == "":
            raise InvalidAuthJWTPayloadError

        return AuthJWTPayload(orcid_id)
