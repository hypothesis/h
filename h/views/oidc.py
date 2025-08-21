"""
Views used in our implementation of OpenID Connect (OIDC).

https://openid.net/specs/openid-connect-core-1_0.html
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Literal
from urllib.parse import urlencode, urlparse, urlunparse

import sentry_sdk
from h_pyramid_sentry import report_exception
from pyramid.httpexceptions import HTTPForbidden, HTTPFound
from pyramid.view import (
    exception_view_config,
    notfound_view_config,
    view_config,
    view_defaults,
)

from h.models.user_identity import IdentityProvider
from h.schemas import ValidationError
from h.schemas.oauth import InvalidOAuth2StateParamError, OAuth2RedirectSchema
from h.services import OIDCService
from h.services.exceptions import ExternalRequestError
from h.services.jwt import JWTAudience, JWTDecodeError, JWTIssuer
from h.views.account_signup import encode_idinfo_token, redirect_url
from h.views.exceptions import UnexpectedRouteError
from h.views.helpers import login

if TYPE_CHECKING:
    from pyramid.request import Request

    from h.models import User


STATE_SESSIONKEY_FMT = "oidc.state.{provider}"


class AccessDeniedError(Exception):
    """The user denied us access to their identity."""


class UserConflictError(Exception):
    """A different Hypothesis user is already connected to this identity."""


ActionType = Literal["connect", "login"]


@dataclass
class OIDCState:
    """The JWT payload of an OpenID Connect `state` param."""

    action: ActionType
    """The action that triggered the OIDC flow.

    For example "connect" when connecting a provider unique ID to an existing
    Hypothesis account, or "login" when using a provider to log in to
    Hypothesis
    """

    rfp: str
    """A Request Forgery Protection (RFP) token to protect against CSRF attacks.

    The claim name "rfp" is compatible with
    https://datatracker.ietf.org/doc/html/draft-bradley-oauth-jwt-encoded-state-09
    """

    next_url: str | None
    """The URL to redirect the browser to after successfully logging in."""

    @classmethod
    def make(cls, action: ActionType, next_url: str | None = None):
        """Return a new OIDCState with the given `action` and a random `rfp`."""
        return cls(action, secrets.token_hex(), next_url)


@dataclass
class OIDCConnectAndLoginViewsSettings:
    """Per-route settings for OIDCConnectAndLoginViews."""

    state_sessionkey: str
    """The key that we use for storing the OAuth/OIDC state in the session.

    When we pass a `state` query param to an OAuth/OIDC authorization service
    we also store a copy of that state param in the browser's session cookie
    for request forgery protection: when the authorization server sends the
    `state` param back to us we check that it matches the copy in the session.

    state_sessionkey is the key that we use for the state in Pyramid's session
    dict. We use a different state_sessionkey for each identity provider to
    avoid any crossed wires between different providers.

    """

    issuer: JWTIssuer
    """The `issuer` string for the OAuth/OIDC state JWT.

    We use a different JWT issuer for each identity provider. This is useful
    for debugging and also allows the code consuming the JWT to potentially
    change its behaviour depending on the provider.

    """

    audience: JWTAudience
    """The `audience` string for OAuth/OIDC state JWTs.

    We use a different JWT audience for each identity provider to prevent JWT
    meant for one provider getting used for another provider.

    """

    client_id: str
    """Our OAuth/OIDC client_id for this provider."""

    authorization_url: str
    """The URL of the provider's OIDC authorization endpoint.

    This is the URL that we redirect the browser to in order to kick off the
    OAuth/OIDC authorization flow.
    """
    redirect_uri: str
    """Our OAuth/OIDC redirect_uri for this provider.

    This is the URL that the provider's authorization server redirects the
    browser back to after the user authorizes us to access their account.
    """

    action: ActionType
    """The action that triggered the OIDC flow.

    For example "connect" when connecting a provider unique ID to an existing
    Hypothesis account, or "login" when using a provider to log in to
    Hypothesis
    """


@view_defaults(request_method="GET")
class OIDCConnectAndLoginViews:
    def __init__(self, request: Request) -> None:
        self._request = request
        self._jwt_service = request.find_service(name="jwt")

    @property
    def settings(self):
        """Return the per-route OIDCConnectAndLoginViewsSettings for the current request."""

        route_name = self._request.matched_route.name

        match route_name:
            case "oidc.connect.orcid" | "oidc.connect.google" | "oidc.connect.facebook":
                action = "connect"
            case "oidc.login.orcid" | "oidc.login.google" | "oidc.login.facebook":
                action = "login"
            case _:
                raise UnexpectedRouteError(route_name)

        settings = self._request.registry.settings

        match route_name:
            case "oidc.connect.orcid" | "oidc.login.orcid":
                return OIDCConnectAndLoginViewsSettings(
                    state_sessionkey=STATE_SESSIONKEY_FMT.format(provider="orcid"),
                    issuer=JWTIssuer.OIDC_CONNECT_OR_LOGIN_ORCID,
                    audience=JWTAudience.OIDC_REDIRECT_ORCID,
                    client_id=settings["oidc_clientid_orcid"],
                    authorization_url=settings["oidc_authorizationurl_orcid"],
                    redirect_uri=self._request.route_url("oidc.redirect.orcid"),
                    action=action,
                )
            case "oidc.connect.google" | "oidc.login.google":  # pragma: no cover
                return OIDCConnectAndLoginViewsSettings(
                    state_sessionkey=STATE_SESSIONKEY_FMT.format(provider="google"),
                    issuer=JWTIssuer.OIDC_CONNECT_OR_LOGIN_GOOGLE,
                    audience=JWTAudience.OIDC_REDIRECT_GOOGLE,
                    client_id=settings["oidc_clientid_google"],
                    authorization_url=settings["oidc_authorizationurl_google"],
                    redirect_uri=self._request.route_url("oidc.redirect.google"),
                    action=action,
                )
            case "oidc.connect.facebook" | "oidc.login.facebook":  # pragma: no cover
                return OIDCConnectAndLoginViewsSettings(
                    state_sessionkey=STATE_SESSIONKEY_FMT.format(provider="facebook"),
                    issuer=JWTIssuer.OIDC_CONNECT_OR_LOGIN_FACEBOOK,
                    audience=JWTAudience.OIDC_REDIRECT_FACEBOOK,
                    client_id=settings["oidc_clientid_facebook"],
                    authorization_url=settings["oidc_authorizationurl_facebook"],
                    redirect_uri=self._request.route_url("oidc.redirect.facebook"),
                    action=action,
                )
            case _:  # pragma: nocover
                raise UnexpectedRouteError(route_name)

    @view_config(is_authenticated=True, route_name="oidc.connect.orcid")
    @view_config(is_authenticated=True, route_name="oidc.connect.google")
    @view_config(is_authenticated=True, route_name="oidc.connect.facebook")
    @view_config(is_authenticated=False, route_name="oidc.login.orcid")
    @view_config(is_authenticated=False, route_name="oidc.login.google")
    @view_config(is_authenticated=False, route_name="oidc.login.facebook")
    def connect_or_login(self):
        state = self._jwt_service.encode_symmetric(
            OIDCState.make(self.settings.action, self._request.params.get("next")),
            expires_in=timedelta(hours=1),
            issuer=self.settings.issuer,
            audience=self.settings.audience,
        )
        self._request.session[self.settings.state_sessionkey] = state

        if self._request.matched_route.name in (
            "oidc.connect.facebook",
            "oidc.login.facebook",
        ):
            # Facebook doesn't require the `profile` scope: it sends us the
            # user's name without it. If you do send the `profile` scope to
            # Facebook it errors out.
            scope = "openid email"  # pragma: no cover
        else:
            # Other providers require the `profile` scope otherwise they don't
            # send us the user's name.
            scope = "openid email profile"

        return HTTPFound(
            location=urlunparse(
                urlparse(self.settings.authorization_url)._replace(
                    query=urlencode(
                        {
                            "client_id": self.settings.client_id,
                            "response_type": "code",
                            "redirect_uri": self.settings.redirect_uri,
                            "state": state,
                            "scope": scope,
                        }
                    )
                )
            )
        )

    @notfound_view_config(
        renderer="h:templates/notfound.html.jinja2",
        append_slash=True,
        route_name="oidc.connect.orcid",
    )
    @notfound_view_config(
        renderer="h:templates/notfound.html.jinja2",
        append_slash=True,
        route_name="oidc.connect.google",
    )
    @notfound_view_config(
        renderer="h:templates/notfound.html.jinja2",
        append_slash=True,
        route_name="oidc.connect.facebook",
    )
    def notfound(self):
        self._request.response.status_int = 401
        return {}

    # It's possible to try to log in while already logged in. For example: open
    # the /login or /signup page but don't click anything yet, then open a new
    # tab and log in, then return to the first tab and try to start a login
    # flow. This view is called in these cases.
    @view_config(route_name="oidc.login.orcid", is_authenticated=True)
    @view_config(route_name="oidc.login.google", is_authenticated=True)
    @view_config(route_name="oidc.login.facebook", is_authenticated=True)
    def login_already_authenticated(self):
        return HTTPFound(
            self._request.route_url(
                "activity.user_search", username=self._request.user.username
            )
        )


@dataclass
class OIDCRedirectViewsSettings:
    """Per-route settings for OIDCRedirectViews."""

    provider_name: str
    jwt_issuer: JWTIssuer
    state_sessionkey: str
    state_jwtaudience: JWTAudience
    idinfo_jwtaudience: JWTAudience
    provider: IdentityProvider
    success_message: str
    signup_route_name: str


class UnexpectedActionError(Exception):
    def __init__(self, action):
        super().__init__(
            f"Received a JWT state param with an unexpected action: {action}"
        )


@view_defaults(request_method="GET")
class OIDCRedirectViews:
    def __init__(self, context, request: Request) -> None:
        self._context = context
        self._request = request
        self._oidc_service = request.find_service(OIDCService)
        self._user_service = request.find_service(name="user")
        self._jwt_service = request.find_service(name="jwt")

    @property
    def settings(self):
        """Return the per-route OIDCConnectAndLoginViewsSettings for the current request."""

        route_name = self._request.matched_route.name

        match route_name:
            case "oidc.redirect.orcid":
                return OIDCRedirectViewsSettings(
                    provider_name="ORCID",
                    jwt_issuer=JWTIssuer.OIDC_REDIRECT_ORCID,
                    state_sessionkey=STATE_SESSIONKEY_FMT.format(provider="orcid"),
                    state_jwtaudience=JWTAudience.OIDC_REDIRECT_ORCID,
                    idinfo_jwtaudience=JWTAudience.SIGNUP_ORCID,
                    provider=IdentityProvider.ORCID,
                    success_message="ORCID iD connected ✓",
                    signup_route_name="signup.orcid",
                )
            case "oidc.redirect.google":  # pragma: no cover
                return OIDCRedirectViewsSettings(
                    provider_name="Google",
                    jwt_issuer=JWTIssuer.OIDC_REDIRECT_GOOGLE,
                    state_sessionkey=STATE_SESSIONKEY_FMT.format(provider="google"),
                    state_jwtaudience=JWTAudience.OIDC_REDIRECT_GOOGLE,
                    idinfo_jwtaudience=JWTAudience.SIGNUP_GOOGLE,
                    provider=IdentityProvider.GOOGLE,
                    success_message="Google account connected",
                    signup_route_name="signup.google",
                )
            case "oidc.redirect.facebook":  # pragma: no cover
                return OIDCRedirectViewsSettings(
                    provider_name="Facebook",
                    jwt_issuer=JWTIssuer.OIDC_REDIRECT_FACEBOOK,
                    state_sessionkey=STATE_SESSIONKEY_FMT.format(provider="facebook"),
                    state_jwtaudience=JWTAudience.OIDC_REDIRECT_FACEBOOK,
                    idinfo_jwtaudience=JWTAudience.SIGNUP_FACEBOOK,
                    provider=IdentityProvider.FACEBOOK,
                    success_message="Facebook account connected",
                    signup_route_name="signup.facebook",
                )
            case _:
                raise UnexpectedRouteError(route_name)

    @view_config(route_name="oidc.redirect.orcid")
    @view_config(route_name="oidc.redirect.google")
    @view_config(route_name="oidc.redirect.facebook")
    def redirect(self):
        try:
            expected_state = self._request.session.pop(self.settings.state_sessionkey)
        except KeyError as err:
            raise InvalidOAuth2StateParamError from err

        try:
            validated_params = OAuth2RedirectSchema.validate(
                dict(self._request.params), expected_state
            )
        except ValidationError as err:
            if self._request.params.get("error") == "access_denied":
                # The user clicked the deny button on the provider's page.
                raise AccessDeniedError from err

            # We received an invalid or unexpected redirect from the provider.
            raise

        decoded_state = self._jwt_service.decode_symmetric(
            validated_params["state"],
            audience=self.settings.state_jwtaudience,
            payload_class=OIDCState,
        )

        if decoded_state.action == "connect" and not self._request.is_authenticated:
            # You must be logged in to connect an identity to your existing
            # Hypothesis account.
            raise HTTPForbidden

        if decoded_state.action == "login" and self._request.is_authenticated:
            # You must be logged out in order to log in.
            raise HTTPForbidden

        # Get the user's provider unique ID from the provider.
        decoded_idtoken = self._oidc_service.get_decoded_idtoken(
            self.settings.provider, validated_params["code"]
        )

        # Get the existing Hypothesis account that's already connected to this
        # provider unique ID, if any.
        user = self._user_service.fetch_by_identity(
            self.settings.provider, provider_unique_id=decoded_idtoken["sub"]
        )

        action = decoded_state.action

        match action:
            case "connect":
                return self.connect_identity(decoded_idtoken, user)
            case "login":
                return self.log_in_with_identity(
                    decoded_idtoken, user, decoded_state.next_url
                )
            case _:
                raise UnexpectedActionError(action)

    def connect_identity(self, decoded_idtoken: dict, user: User | None):
        """Connect the user's third-party identity to their Hypothesis account.

        Do nothing if the third-party identity (represented by the given
        `decoded_idtoken`) is already connected to `user`.

        """
        if user and user != self._request.user:
            # Oops, this identity is already connected to a different
            # Hypothesis account.
            raise UserConflictError

        if not user:
            # This identity isn't connected to a Hypothesis account yet. Let's
            # go ahead and connect it to the user's account.
            self._oidc_service.add_identity(
                self._request.user,
                self.settings.provider,
                provider_unique_id=decoded_idtoken["sub"],
                email=decoded_idtoken.get("email"),
                name=decoded_idtoken.get("name"),
                given_name=decoded_idtoken.get("given_name"),
                family_name=decoded_idtoken.get("family_name"),
            )

        self._request.session.flash(self.settings.success_message, "success")
        return HTTPFound(self._request.route_url("account"))

    def log_in_with_identity(self, decoded_idtoken: dict, user, next_url: str):
        if not user:
            # There's no Hypothesis account for this provider unique ID yet.
            # Redirect to the "Sign up to Hypothesis with <PROVIDER>" page to
            # create a new account.
            return HTTPFound(
                self._request.route_url(
                    self.settings.signup_route_name,
                    _query=encode_idinfo_token(
                        self._jwt_service,
                        decoded_idtoken["sub"],
                        decoded_idtoken.get("email"),
                        decoded_idtoken.get("name"),
                        decoded_idtoken.get("given_name"),
                        decoded_idtoken.get("family_name"),
                        self.settings.jwt_issuer,
                        self.settings.idinfo_jwtaudience,
                        next_url,
                        self._request.session,
                    ),
                )
            )

        headers = login(user, self._request)

        return HTTPFound(redirect_url(self._request, user, next_url), headers=headers)

    @notfound_view_config(
        renderer="h:templates/notfound.html.jinja2",
        append_slash=True,
        route_name="oidc.redirect.orcid",
    )
    @notfound_view_config(
        renderer="h:templates/notfound.html.jinja2",
        append_slash=True,
        route_name="oidc.redirect.google",
    )
    @notfound_view_config(
        renderer="h:templates/notfound.html.jinja2",
        append_slash=True,
        route_name="oidc.redirect.facebook",
    )
    def notfound(self):
        self._request.response.status_int = 401
        return {}

    @exception_view_config(context=ValidationError, route_name="oidc.redirect.orcid")
    @exception_view_config(context=ValidationError, route_name="oidc.redirect.google")
    @exception_view_config(context=ValidationError, route_name="oidc.redirect.facebook")
    def invalid(self):
        report_exception(self._context)
        self._request.session.flash(
            f"Received an invalid redirect from {self.settings.provider_name}!", "error"
        )
        return HTTPFound(location=self._request.route_url("account"))

    @exception_view_config(context=JWTDecodeError, route_name="oidc.redirect.orcid")
    @exception_view_config(context=JWTDecodeError, route_name="oidc.redirect.google")
    @exception_view_config(context=JWTDecodeError, route_name="oidc.redirect.facebook")
    def invalid_token(self):
        report_exception(self._context)
        self._request.session.flash(
            f"Received an invalid token from {self.settings.provider_name}!", "error"
        )
        return HTTPFound(location=self._request.route_url("account"))

    @exception_view_config(context=AccessDeniedError, route_name="oidc.redirect.orcid")
    @exception_view_config(context=AccessDeniedError, route_name="oidc.redirect.google")
    @exception_view_config(
        context=AccessDeniedError, route_name="oidc.redirect.facebook"
    )
    def denied(self):
        self._request.session.flash("The user clicked the deny button!", "error")
        return HTTPFound(location=self._request.route_url("account"))

    @exception_view_config(
        context=ExternalRequestError, route_name="oidc.redirect.orcid"
    )
    @exception_view_config(
        context=ExternalRequestError, route_name="oidc.redirect.google"
    )
    @exception_view_config(
        context=ExternalRequestError, route_name="oidc.redirect.facebook"
    )
    def external_request(self):
        handle_external_request_error(self._context)
        self._request.session.flash(
            f"Request to {self.settings.provider_name} failed!", "error"
        )
        return HTTPFound(location=self._request.route_url("account"))

    @exception_view_config(context=UserConflictError, route_name="oidc.redirect.orcid")
    @exception_view_config(context=UserConflictError, route_name="oidc.redirect.google")
    @exception_view_config(
        context=UserConflictError, route_name="oidc.redirect.facebook"
    )
    def user_conflict_error(self):
        self._request.session.flash(
            f"A different Hypothesis user is already connected to this {self.settings.provider_name} account!",
            "error",
        )
        return HTTPFound(location=self._request.route_url("account"))


def handle_external_request_error(exception: ExternalRequestError) -> None:
    sentry_sdk.set_context(
        "request",
        {
            "method": exception.method,
            "url": exception.url,
            "body": exception.request_body,
        },
    )
    sentry_sdk.set_context(
        "response",
        {
            "status_code": exception.status_code,
            "reason": exception.reason,
            "body": exception.response_body,
        },
    )
    if exception.validation_errors:
        sentry_sdk.set_context("validation_errors", exception.validation_errors)

    report_exception(exception)
