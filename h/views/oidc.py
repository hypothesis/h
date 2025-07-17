"""
Views used in our implementation of OpenID Connect (OIDC).

https://openid.net/specs/openid-connect-core-1_0.html
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Literal
from urllib.parse import urlencode, urlunparse

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
from h.services import ORCIDClientService
from h.services.exceptions import ExternalRequestError
from h.services.jwt import JWTAudiences, JWTDecodeError, JWTIssuers
from h.views.helpers import login

if TYPE_CHECKING:
    from pyramid.request import Request

    from h.models import User


ORCID_STATE_SESSION_KEY = "oidc.state.orcid"


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

    For example "connect" when connecting an ORCID iD to an existing Hypothesis
    account, or "login" when using ORCID to log in to Hypothesis
    """

    rfp: str
    """A Request Forgery Protection (RFP) token to protect against CSRF attacks.

    The claim name "rfp" is compatible with
    https://datatracker.ietf.org/doc/html/draft-bradley-oauth-jwt-encoded-state-09
    """

    @classmethod
    def make(cls, action: ActionType):
        """Return a new OIDCState with the given `action` and a random `rfp`."""
        return cls(action, secrets.token_hex())


@view_defaults(request_method="GET")
class ORCIDConnectAndLoginViews:
    def __init__(self, request: Request) -> None:
        self._request = request
        self._jwt_service = request.find_service(name="jwt")

    @view_config(is_authenticated=True, route_name="oidc.connect.orcid")
    @view_config(is_authenticated=False, route_name="oidc.login.orcid")
    def connect_or_login(self):
        host = self._request.registry.settings["orcid_host"]
        client_id = self._request.registry.settings["orcid_client_id"]

        actions = {"oidc.connect.orcid": "connect", "oidc.login.orcid": "login"}
        action = actions[self._request.matched_route.name]

        state = self._jwt_service.encode_symmetric(
            OIDCState.make(action),
            expires_in=timedelta(hours=1),
            issuer=JWTIssuers.OIDC_CONNECT_OR_LOGIN_ORCID,
            audience=JWTAudiences.OIDC_REDIRECT_ORCID,
        )
        self._request.session[ORCID_STATE_SESSION_KEY] = state

        params = {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": self._request.route_url("oidc.redirect.orcid"),
            "state": state,
            "scope": "openid",
        }
        return HTTPFound(
            location=urlunparse(
                (
                    "https",
                    host,
                    "oauth/authorize",
                    "",
                    urlencode(params),
                    "",
                )
            )
        )

    @notfound_view_config(
        renderer="h:templates/notfound.html.jinja2",
        append_slash=True,
        route_name="oidc.connect.orcid",
    )
    def notfound(self):
        self._request.response.status_int = 401
        return {}

    # It's possible to try to log in while already logged in. For example: open
    # the /login or /signup page but don't click anything yet, then open a new
    # tab and log in, then return to the first tab and try to start a login
    # flow. This view is called in these cases.
    @view_config(route_name="oidc.login.orcid", is_authenticated=True)
    def login_already_authenticated(self):
        return HTTPFound(
            self._request.route_url(
                "activity.user_search", username=self._request.user.username
            )
        )


@view_defaults(request_method="GET", route_name="oidc.redirect.orcid")
class ORCIDRedirectViews:
    def __init__(self, context, request: Request) -> None:
        self._context = context
        self._request = request
        self._orcid_client = request.find_service(ORCIDClientService)
        self._user_service = request.find_service(name="user")
        self._jwt_service = request.find_service(name="jwt")

    @view_config()
    def redirect(self):
        try:
            expected_state = self._request.session.pop(ORCID_STATE_SESSION_KEY)
        except KeyError as err:
            raise InvalidOAuth2StateParamError from err

        try:
            validated_params = OAuth2RedirectSchema.validate(
                dict(self._request.params), expected_state
            )
        except ValidationError as err:
            if self._request.params.get("error") == "access_denied":
                # The user clicked the deny button on ORCID's page.
                raise AccessDeniedError from err

            # We received an invalid or unexpected redirect from ORCID.
            raise

        decoded_state = self._jwt_service.decode_symmetric(
            validated_params["state"],
            audience=JWTAudiences.OIDC_REDIRECT_ORCID,
            payload_class=OIDCState,
        )

        if decoded_state.action == "connect" and not self._request.is_authenticated:
            # You must be logged in to connect an identity to your existing
            # Hypothesis account.
            raise HTTPForbidden

        if decoded_state.action == "login" and self._request.is_authenticated:
            # You must be logged out in order to log in.
            raise HTTPForbidden

        # Get the user's ORCID iD from ORCID.
        orcid_id = self._orcid_client.get_orcid(validated_params["code"])

        # Get the existing Hypothesis account that's already connected to this
        # ORCID iD, if any.
        user = self._user_service.fetch_by_identity(IdentityProvider.ORCID, orcid_id)

        actions = {
            "connect": self.connect_orcid_id,
            "login": self.log_in_with_orcid,
        }
        action_method = actions[decoded_state.action]
        return action_method(orcid_id, user)

    def connect_orcid_id(self, orcid_id: str, user: User | None):
        """Connect the user's ORCID iD to their Hypothesis account.

        Do nothing if `orcid_id` is already connected to `user`.

        """
        if user and user != self._request.user:
            # Oops, this ORCID iD is already connected to a different
            # Hypothesis account.
            raise UserConflictError

        if not user:
            # This ORCID iD isn't connected to a Hypothesis account yet.
            # Let's go ahead and connect it to the user's account.
            self._orcid_client.add_identity(self._request.user, orcid_id)

        self._request.session.flash("ORCID iD connected ✓", "success")
        return HTTPFound(self._request.route_url("account"))

    def log_in_with_orcid(self, orcid_id: str, user):
        if not user:
            msg = "Not implemented yet"
            raise RuntimeError(msg)

        del orcid_id

        headers = login(user, self._request)

        return HTTPFound(
            self._request.route_url("activity.user_search", username=user.username),
            headers=headers,
        )

    @notfound_view_config(
        renderer="h:templates/notfound.html.jinja2", append_slash=True
    )
    def notfound(self):
        self._request.response.status_int = 401
        return {}

    @exception_view_config(context=ValidationError)
    def invalid(self):
        report_exception(self._context)
        self._request.session.flash("Received an invalid redirect from ORCID!", "error")
        return HTTPFound(location=self._request.route_url("account"))

    @exception_view_config(context=JWTDecodeError)
    def invalid_token(self):
        report_exception(self._context)
        self._request.session.flash("Received an invalid token from ORCID!", "error")
        return HTTPFound(location=self._request.route_url("account"))

    @exception_view_config(context=AccessDeniedError)
    def denied(self):
        self._request.session.flash("The user clicked the deny button!", "error")
        return HTTPFound(location=self._request.route_url("account"))

    @exception_view_config(context=ExternalRequestError)
    def external_request(self):
        handle_external_request_error(self._context)
        self._request.session.flash("Request to ORCID failed!", "error")
        return HTTPFound(location=self._request.route_url("account"))

    @exception_view_config(context=UserConflictError)
    def user_conflict_error(self):
        self._request.session.flash(
            "A different Hypothesis user is already connected to this ORCID iD!",
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
