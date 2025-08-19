import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlparse, urlunparse

from deform import ValidationFailure
from h_pyramid_sentry import report_exception
from pyramid.csrf import get_csrf_token
from pyramid.httpexceptions import HTTPFound
from pyramid.interfaces import ISession
from pyramid.view import exception_view_config, view_config, view_defaults

from h import i18n
from h.accounts.schemas import SignupSchema, SocialLoginSignupSchema
from h.models import User
from h.models.user_identity import IdentityProvider
from h.services.jwt import JWTAudience, JWTDecodeError, JWTIssuer, JWTService
from h.services.user_signup import (
    EmailConflictError,
    IdentityConflictError,
    UsernameConflictError,
)
from h.views.exceptions import UnexpectedRouteError
from h.views.helpers import login, logout

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

        signup_service.signup(
            username=appstruct["username"],
            email=appstruct["email"],
            password=appstruct["password"],
            privacy_accepted=datetime.now(UTC),
            comms_opt_in=appstruct["comms_opt_in"],
        )

        return {
            "js_config": self.js_config,
            "heading": _("Account registration successful"),
        }

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
    @exception_view_config(
        UsernameConflictError,
        route_name="signup.email",
        request_method="POST",
        renderer="h:templates/accounts/signup-post.html.jinja2",
    )
    @exception_view_config(
        EmailConflictError,
        route_name="signup.email",
        request_method="POST",
        renderer="h:templates/accounts/signup-post.html.jinja2",
    )
    def validation_failure(self):
        self.request.response.status_int = 400

        # A username or email conflict can happen *after* request validation,
        # at the database level when trying to create the new user account.
        #
        # This can happen when multiple simultaneous requests try to create an
        # account with the same username or email address: at validation time
        # the username and email address are not taken so the request continues
        # and tries to add a new user to the DB, but by the time we try to
        # flush the DB session a simultaneous request has already created a
        # user with the same username or email address.
        #
        # Set `errors` to the same errors dict that self.context.error.asdict()
        # returns if self.context is a ValidationFailure due to the username or
        # email address already being taken.
        # This will produce the same error response as if the username or email
        # address already been taken at request validation time.
        if isinstance(self.context, UsernameConflictError):
            errors = {"username": "This username is already taken."}
        elif isinstance(self.context, EmailConflictError):
            errors = {"email": "This email address is already taken."}
        else:
            errors = self.context.error.asdict()

        return {
            "js_config": {
                **self.js_config,
                "form": {
                    "errors": errors,
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
            "forOAuth": bool(self.request.params.get("for_oauth")),
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
    """The user's unique ID from the third-party provider."""

    rfp: str
    """A Request Forgery Protection (RFP) token to protect against CSRF attacks.

    The claim name "rfp" is compatible with
    https://datatracker.ietf.org/doc/html/draft-bradley-oauth-jwt-encoded-state-09
    """

    email: str | None = None
    name: str | None = None
    given_name: str | None = None
    family_name: str | None = None

    next_url: str | None = None
    """The URL to redirect to after successfully logging in."""

    @property
    def display_name(self):
        if self.name:
            return self.name

        if self.given_name and self.family_name:
            return f"{self.given_name} {self.family_name}"

        if self.given_name:
            return self.given_name

        return None


@dataclass
class SocialLoginSignupViewsSettings:
    """Per-route settings for SocialLoginSignupViews."""

    provider: IdentityProvider
    provider_name: str
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
        self.user_service = request.find_service(name="user")

    @property
    def settings(self) -> SocialLoginSignupViewsSettings:
        """Return the per-route SocialLoginSignupViewsSettings for the current request."""

        route_name = self.request.matched_route.name

        match route_name:
            case "signup.orcid":
                return SocialLoginSignupViewsSettings(
                    provider=IdentityProvider.ORCID,
                    provider_name="ORCID",
                    issuer=JWTIssuer.SIGNUP_VALIDATION_FAILURE_ORCID,
                    audience=JWTAudience.SIGNUP_ORCID,
                )
            case "signup.google":  # pragma: no cover
                return SocialLoginSignupViewsSettings(
                    provider=IdentityProvider.GOOGLE,
                    provider_name="Google",
                    issuer=JWTIssuer.SIGNUP_VALIDATION_FAILURE_GOOGLE,
                    audience=JWTAudience.SIGNUP_GOOGLE,
                )
            case "signup.facebook":  # pragma: no cover
                return SocialLoginSignupViewsSettings(
                    provider=IdentityProvider.FACEBOOK,
                    provider_name="Facebook",
                    issuer=JWTIssuer.SIGNUP_VALIDATION_FAILURE_FACEBOOK,
                    audience=JWTAudience.SIGNUP_FACEBOOK,
                )
            case _:  # pragma: nocover
                raise UnexpectedRouteError(route_name)

    @view_config(request_method="GET", route_name="signup.orcid")
    @view_config(request_method="GET", route_name="signup.google")
    @view_config(request_method="GET", route_name="signup.facebook")
    def get(self):
        idinfo = self.decode_idinfo()

        # If we get to this view there normally won't be an existing account
        # already connected to the user's third-party identity: if such an
        # account existed the user would have been logged into it rather than
        # being redirected to this signup page.
        #
        # But concurrent signup requests can mean that we get here and find
        # that a connected account already exists in the DB.
        #
        # We *could* log the user in to the existing account at this point. But
        # I think this case is going to be pretty rare so for simplicity's sake
        # I'm just going to raise an error.
        if self.user_service.fetch_by_identity(
            self.settings.provider, provider_unique_id=idinfo.sub
        ):
            raise IdentityConflictError

        # Error if there's already a Hypothesis account with the same email
        # address as the user's third-party identity.
        #
        # This can happen if the user manually creates an account with the same
        # email address as they use with their third-party identity, and then
        # later tries to log in or sign up with that third-party identity.
        #
        # It can also happen if there are concurrent signup requests.
        if User.get_by_email(
            self.request.db, idinfo.email, self.request.default_authority
        ):
            raise EmailConflictError

        return {"js_config": self.js_config(idinfo.sub, idinfo.email)}

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
            email=idinfo.email,
            display_name=idinfo.display_name,
            password=None,
            privacy_accepted=datetime.now(UTC),
            comms_opt_in=bool(appstruct.get("comms_opt_in", False)),
            require_activation=False,
            identities=[
                {
                    "provider": self.settings.provider,
                    "provider_unique_id": idinfo.sub,
                    "email": idinfo.email,
                    "name": idinfo.name,
                    "given_name": idinfo.given_name,
                    "family_name": idinfo.family_name,
                }
            ],
        )

        return HTTPFound(
            redirect_url(self.request, user, idinfo.next_url),
            headers=login(user, self.request),
        )

    @exception_view_config(
        context=EmailConflictError,
        route_name="signup.orcid",
        renderer="h:templates/error.html.jinja2",
    )
    @exception_view_config(
        context=EmailConflictError,
        route_name="signup.google",
        renderer="h:templates/error.html.jinja2",
    )
    @exception_view_config(
        context=EmailConflictError,
        route_name="signup.facebook",
        renderer="h:templates/error.html.jinja2",
    )
    def email_conflict_error(self):
        # Decode the idinfo *before* generating the logout headers because
        # calling logout() invalidates the session which removes the idinfo
        # token's rfp (request forgery protection) token from the session
        # meaning trying to decode the idinfo token will now fail.
        idinfo = self.decode_idinfo()

        # Generate the logout headers *before* setting the flash message
        # because calling logout() invalidates the session which deletes any
        # flash messages.
        headers = logout(self.request)

        self.request.session.flash(
            f"There's already a Hypothesis account with your {self.settings.provider_name} email address."
            " Try logging in or resetting your password."
            f" Once logged in you can connect {self.settings.provider_name} in your account settings.",
            "error",
        )

        return HTTPFound(
            self.request.route_url("login", _query={"username": idinfo.email}),
            headers=headers,
        )

    @exception_view_config(
        context=IdentityConflictError,
        route_name="signup.orcid",
        renderer="h:templates/error.html.jinja2",
    )
    @exception_view_config(
        context=IdentityConflictError,
        route_name="signup.google",
        renderer="h:templates/error.html.jinja2",
    )
    @exception_view_config(
        context=IdentityConflictError,
        route_name="signup.facebook",
        renderer="h:templates/error.html.jinja2",
    )
    def identity_conflict_error(self):
        # Generate the logout headers *before* setting the flash message
        # because calling logout() invalidates the session which deletes any
        # flash messages.
        headers = logout(self.request)

        self.request.session.flash(
            f"There's already a Hypothesis account connected to your {self.settings.provider_name} account. Try logging in.",
            "error",
        )

        return HTTPFound(self.request.route_url("login"), headers=headers)

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
    @exception_view_config(context=UsernameConflictError, route_name="signup.orcid")
    @exception_view_config(context=UsernameConflictError, route_name="signup.google")
    @exception_view_config(context=UsernameConflictError, route_name="signup.facebook")
    def validation_failure(self):
        idinfo = self.decode_idinfo()
        self.request.response.status_int = 400

        # When reloading the page prefill the form with the previously submitted values.
        form_data = {
            "username": self.request.POST.get("username", ""),
            "privacy_accepted": self.request.POST.get("privacy_accepted", "") == "true",
            "comms_opt_in": self.request.POST.get("comms_opt_in", "") == "true",
        }

        if isinstance(self.context, UsernameConflictError):
            # A username conflict happened *after* request validation, at the
            # database level when trying to create the new user account.
            #
            # This can happen when multiple simultaneous requests try to create
            # an account with the same username--at validation time the
            # username is not taken so the request continues and tries to add a
            # new user to the DB, but by the time we try to flush the DB
            # session a simultaneous request has already created a user with
            # the same username.
            #
            # Set `errors` to the same errors dict that
            # self.context.error.asdict() returns if self.context is a
            # ValidationFailure due to the username already being taken.
            # This will produce the same error response as if the username had
            # already been taken at request validation time.
            errors = {"username": "This username is already taken."}
        else:
            errors = self.context.error.asdict()

        return {
            "js_config": {
                **self.js_config(idinfo.sub, idinfo.email),
                "form": {"errors": errors, "data": form_data},
            }
        }

    def js_config(self, provider_unique_id, email):
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
            "identity": {
                "provider_unique_id": provider_unique_id,
                "email": email,
            },
        }

    def decode_idinfo(self):
        return decode_idinfo_token(
            self.jwt_service,
            self.request.params["idinfo"],
            audience=self.settings.audience,
            session=self.request.session,
        )


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


IDINFO_RFP_SESSIONKEY_FMT = "idinfo.rfp.{audience}"


def encode_idinfo_token(  # noqa: PLR0913
    jwt_service: JWTService,
    provider_unique_id: str,
    email: str | None,
    name: str | None,
    given_name: str | None,
    family_name: str | None,
    issuer: JWTIssuer,
    audience: JWTAudience,
    next_url: str,
    session: ISession,
):
    rfp = secrets.token_hex()

    session[IDINFO_RFP_SESSIONKEY_FMT.format(audience=audience)] = rfp

    return {
        "idinfo": jwt_service.encode_symmetric(
            IDInfo(
                provider_unique_id,
                rfp,
                email,
                name,
                given_name,
                family_name,
                next_url=next_url,
            ),
            expires_in=timedelta(hours=1),
            issuer=issuer,
            audience=audience,
        ),
    }


def decode_idinfo_token(
    jwt_service: JWTService,
    idinfo_token: str,
    audience: JWTAudience,
    session: ISession,
):
    try:
        expected_rfp = session[IDINFO_RFP_SESSIONKEY_FMT.format(audience=audience)]
    except KeyError as err:
        raise IDInfoJWTDecodeError from err

    try:
        idinfo = jwt_service.decode_symmetric(
            idinfo_token,
            audience=audience,
            payload_class=IDInfo,
        )
    except JWTDecodeError as err:
        raise IDInfoJWTDecodeError from err

    if idinfo.rfp != expected_rfp:
        raise IDInfoJWTDecodeError

    return idinfo


def redirect_url(request, user, url):
    """Return the URL to redirect to after successfully logged in.

    The `url` argument is a URL that (ultimately) comes from a `?next=<URL>`
    query param and therefore can't be trusted: we don't want attackers
    crafting URLs with query params that cause us to redirect users to
    malicious websites.

    This function therefore follows the given `url` only if it matches one of
    an allow-list of known-safe URLs.  Otherwise it returns a default URL
    instead.

    """
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
    next_url = request.params.get("next")
    query = {"next": next_url} if next_url else {}

    if request.params.get("for_oauth"):
        query["for_oauth"] = True

    login_links = {
        "username_or_email": request.route_url("login", _query=query),
    }

    enabled_providers = [
        value.name.lower()
        for value in IdentityProvider
        if request.feature(f"log_in_with_{value.name.lower()}")
    ]

    if enabled_providers:
        for provider in enabled_providers:
            login_links[provider] = request.route_url(
                f"oidc.login.{provider}", _query=query
            )

    urls = js_config.setdefault("urls", {})
    urls["login"] = login_links
    urls["signup"] = request.route_url("signup", _query=query)
