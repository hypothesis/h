from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlparse, urlunparse

from deform import ValidationFailure
from h_pyramid_sentry import report_exception
from pyramid.csrf import get_csrf_token
from pyramid.httpexceptions import HTTPFound
from pyramid.view import exception_view_config, view_config, view_defaults

from h import i18n
from h.accounts.schemas import SignupSchema, SocialLoginSignupSchema
from h.models.user_identity import IdentityProvider
from h.services.exceptions import ConflictError
from h.services.jwt import JWTAudience, JWTDecodeError, JWTIssuer, JWTService
from h.views.exceptions import UnexpectedRouteError
from h.views.helpers import login

_ = i18n.TranslationString


@view_defaults(is_authenticated=False)
class SignupViews:
    def __init__(self, context, request):
        self.context = context
        self.request = request

    @view_config(
        route_name="signup",
        request_method="GET",
        renderer="h:templates/accounts/signup.html.jinja2",
    )
    @view_config(
        route_name="signup.email",
        request_method="GET",
        renderer="h:templates/accounts/signup.html.jinja2",
    )
    def get(self):
        """Render the empty registration form."""
        return {"js_config": self.js_config}

    # "signup" route needed here in case social sign up flags are disabled.
    # This can be removed once the `log_in_with_orcid` flag is removed.
    @view_config(
        route_name="signup",
        request_method="POST",
        renderer="h:templates/accounts/signup-post.html.jinja2",
    )
    @view_config(
        route_name="signup.email",
        request_method="POST",
        renderer="h:templates/accounts/signup-post.html.jinja2",
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
                privacy_accepted=datetime.now(UTC),
                comms_opt_in=appstruct["comms_opt_in"],
            )
        except ConflictError as exc:
            heading = _("Account already registered")
            message = _(f"{exc.args[0]}")  # noqa: INT001

        return {"js_config": self.js_config, "heading": heading, "message": message}

    # For "signup" route, see note in `post` method.
    @exception_view_config(
        ValidationFailure,
        route_name="signup",
        request_method="POST",
        renderer="h:templates/accounts/signup-post.html.jinja2",
    )
    @exception_view_config(
        ValidationFailure,
        route_name="signup.email",
        request_method="POST",
        renderer="h:templates/accounts/signup-post.html.jinja2",
    )
    def validation_failure(self):
        return {
            "js_config": {
                **self.js_config,
                "form": {
                    "errors": self.context.error.asdict(),
                    "data": {
                        "username": self.request.POST.get("username", ""),
                        "email": self.request.POST.get("email", ""),
                        "password": self.request.POST.get("password", ""),
                        "privacy_accepted": self.request.POST.get(
                            "privacy_accepted", ""
                        )
                        == "true",
                        "comms_opt_in": self.request.POST.get("comms_opt_in", "")
                        == "true",
                    },
                },
            }
        }

    @property
    def js_config(self) -> dict[str, Any]:
        feature_service = self.request.find_service(name="feature")

        js_config = {
            "csrfToken": get_csrf_token(self.request),
            "features": {
                "log_in_with_orcid": feature_service.enabled(
                    "log_in_with_orcid", user=None
                ),
                "log_in_with_google": feature_service.enabled(
                    "log_in_with_google", user=None
                ),
                "log_in_with_facebook": feature_service.enabled(
                    "log_in_with_facebook", user=None
                ),
            },
            "form": {},
        }

        inject_login_urls(self.request, js_config)

        return js_config


class IDInfoJWTDecodeError(Exception):
    """Decoding the `idinfo` JWT query param failed."""


@dataclass
class IDInfo:
    """Information about the user's account with a third-party provider.

    When signing up to Hypothesis with a third-party provider ("Sign up with
    Google" etc) the IDInfo class represents the payload of a signed JWT that
    we use to pass information about the user's account with the third-party
    from one route of our app to another when redirecting the browser (we
    include the JWT in a query param).

    The standard JWT `sub` (subject) claim is used to contain the user's unique
    ID from the third-party provider. The JWT spec says that `sub` must be
    locally unique within the context of the issuer (the `iss` claim). We
    achieve this by using a different `iss` for each provider (Google,
    Facebook, etc).

    https://www.rfc-editor.org/rfc/rfc7519#section-4.1.2

    """

    sub: str
    next_url: str | None = None


@dataclass
class SocialLoginSignupViewsSettings:
    """Per-route settings for SocialLoginSignupViews."""

    provider: IdentityProvider
    issuer: JWTIssuer
    audience: JWTAudience


@view_defaults(
    is_authenticated=False,
    request_param="idinfo",
    renderer="h:templates/accounts/signup.html.jinja2",
)
class SocialLoginSignupViews:
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.jwt_service = request.find_service(name="jwt")

    @property
    def settings(self) -> SocialLoginSignupViewsSettings:
        """Return the per-route SocialLoginSignupViewsSettings for the current request."""

        route_name = self.request.matched_route.name

        match route_name:
            case "signup.orcid":
                return SocialLoginSignupViewsSettings(
                    provider=IdentityProvider.ORCID,
                    issuer=JWTIssuer.SIGNUP_VALIDATION_FAILURE_ORCID,
                    audience=JWTAudience.SIGNUP_ORCID,
                )
            case "signup.google":  # pragma: no cover
                return SocialLoginSignupViewsSettings(
                    provider=IdentityProvider.GOOGLE,
                    issuer=JWTIssuer.SIGNUP_VALIDATION_FAILURE_GOOGLE,
                    audience=JWTAudience.SIGNUP_GOOGLE,
                )
            case "signup.facebook":  # pragma: no cover
                return SocialLoginSignupViewsSettings(
                    provider=IdentityProvider.FACEBOOK,
                    issuer=JWTIssuer.SIGNUP_VALIDATION_FAILURE_FACEBOOK,
                    audience=JWTAudience.SIGNUP_FACEBOOK,
                )
            case _:  # pragma: nocover
                raise UnexpectedRouteError(route_name)

    @view_config(request_method="GET", route_name="signup.orcid")
    @view_config(request_method="GET", route_name="signup.google")
    @view_config(request_method="GET", route_name="signup.facebook")
    def get(self):
        return {"js_config": self.js_config(self.decode_idinfo().sub)}

    @view_config(request_method="POST", require_csrf=True, route_name="signup.orcid")
    @view_config(request_method="POST", require_csrf=True, route_name="signup.google")
    @view_config(request_method="POST", require_csrf=True, route_name="signup.facebook")
    def post(self):
        # Decode the user's provider unique ID first so that if decoding this
        # fails the view hasn't already done anything else.
        idinfo = self.decode_idinfo()

        form = self.request.create_form(
            SocialLoginSignupSchema().bind(request=self.request)
        )

        appstruct = form.validate(self.request.POST.items())

        signup_service = self.request.find_service(name="user_signup")

        user = signup_service.signup(
            username=appstruct["username"],
            email=None,
            password=None,
            privacy_accepted=datetime.now(UTC),
            comms_opt_in=bool(appstruct.get("comms_opt_in", False)),
            require_activation=False,
            identities=[
                {
                    "provider": self.settings.provider,
                    "provider_unique_id": idinfo.sub,
                }
            ],
        )

        return HTTPFound(
            redirect_url(self.request, user, idinfo.next_url),
            headers=login(user, self.request),
        )

    @exception_view_config(
        context=IDInfoJWTDecodeError,
        renderer="h:templates/error.html.jinja2",
        route_name="signup.orcid",
    )
    @exception_view_config(
        context=IDInfoJWTDecodeError,
        renderer="h:templates/error.html.jinja2",
        route_name="signup.google",
    )
    @exception_view_config(
        context=IDInfoJWTDecodeError,
        renderer="h:templates/error.html.jinja2",
        route_name="signup.facebook",
    )
    def idinfo_jwt_decode_error(self):
        report_exception(self.context)
        self.request.response.status_int = 403
        return {"error": "Decoding idinfo JWT failed."}

    @exception_view_config(context=ValidationFailure, route_name="signup.orcid")
    @exception_view_config(context=ValidationFailure, route_name="signup.google")
    @exception_view_config(context=ValidationFailure, route_name="signup.facebook")
    def validation_failure(self):
        provider_unique_id = self.decode_idinfo().sub
        self.request.response.status_int = 400

        # When reloading the page prefill the form with the previously submitted values.
        form_data = {
            "username": self.request.POST.get("username", ""),
            "privacy_accepted": self.request.POST.get("privacy_accepted", "") == "true",
            "comms_opt_in": self.request.POST.get("comms_opt_in", "") == "true",
        }

        return {
            "js_config": {
                **self.js_config(provider_unique_id),
                "form": {
                    "errors": self.context.error.asdict(),
                    "data": form_data,
                },
            }
        }

    def js_config(self, provider_unique_id):
        feature_service = self.request.find_service(name="feature")

        return {
            "csrfToken": get_csrf_token(self.request),
            "features": {
                "log_in_with_orcid": feature_service.enabled(
                    "log_in_with_orcid", user=None
                ),
                "log_in_with_google": feature_service.enabled(
                    "log_in_with_google", user=None
                ),
                "log_in_with_facebook": feature_service.enabled(
                    "log_in_with_facebook", user=None
                ),
            },
            "form": {},
            "identity": {"provider_unique_id": provider_unique_id},
        }

    def decode_idinfo(self):
        try:
            idinfo = self.jwt_service.decode_symmetric(
                self.request.params["idinfo"],
                audience=self.settings.audience,
                payload_class=IDInfo,
            )
        except JWTDecodeError as err:
            raise IDInfoJWTDecodeError from err

        return idinfo


# It's possible to try to sign up while already logged in. For example: start
# to signup but don't submit the final form, then open a new tab and log in,
# then return to the first tab and submit the signup form. This view is called
# in these cases.
@view_config(route_name="signup", is_authenticated=True)
@view_config(route_name="signup.orcid", is_authenticated=True)
@view_config(route_name="signup.google", is_authenticated=True)
@view_config(route_name="signup.facebook", is_authenticated=True)
def is_authenticated(request):
    return HTTPFound(
        request.route_url("activity.user_search", username=request.user.username)
    )


def encode_idinfo_token(
    jwt_service: JWTService,
    provider_unique_id: str,
    issuer: JWTIssuer,
    audience: JWTAudience,
    next_url: str,
):
    return {
        "idinfo": jwt_service.encode_symmetric(
            IDInfo(provider_unique_id, next_url=next_url),
            expires_in=timedelta(hours=1),
            issuer=issuer,
            audience=audience,
        ),
    }


def redirect_url(request, user, url):
    default_url = request.route_url("activity.user_search", username=user.username)

    if not url:
        return default_url

    url_without_query_or_fragment = urlunparse(
        urlparse(url)._replace(query=None, fragment=None)
    )

    if url_without_query_or_fragment in [
        request.route_url("oauth_authorize"),
    ]:
        return url

    return default_url


def inject_login_urls(request, js_config):
    enabled_providers = [
        value.name.lower()
        for value in IdentityProvider
        if request.feature(f"log_in_with_{value.name.lower()}")
    ]

    if enabled_providers:
        next_url = request.params.get("next")
        query = {"next": next_url} if next_url else {}
        js_config.setdefault("urls", {})["login"] = {
            provider: request.route_url(f"oidc.login.{provider}", _query=query)
            for provider in enabled_providers
        }
