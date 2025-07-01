import secrets
from urllib.parse import urlencode, urlunparse

import jwt
import sentry_sdk
from h_pyramid_sentry import report_exception
from pyramid.httpexceptions import HTTPFound
from pyramid.request import Request
from pyramid.view import (
    exception_view_config,
    notfound_view_config,
    view_config,
    view_defaults,
)

from h.models.user_identity import IdentityProvider
from h.schemas import ValidationError
from h.schemas.oauth import OAuth2RedirectSchema
from h.services import ORCIDClientService
from h.services.exceptions import ExternalRequestError
from h.services.jwt import TokenValidationError

STATE_SESSION_KEY = "oidc.state.{provider}"
KEY = "not_a_secret"


def encode_oauth2_state_param(action, key):
    return jwt.encode(
        {"rfp": secrets.token_hex(), "action": action}, key, algorithm="HS256"
    )


def decode_oauth2_state_param(state_param, key):
    return jwt.decode(state_param, key, algorithms=["HS256"])


@view_defaults(request_method="GET", route_name="orcid.oauth.authorize")
class AuthorizeViews:
    def __init__(self, request: Request) -> None:
        self._request = request

    @view_config(is_authenticated=True)
    def authorize(self):
        action = self._request.params["action"]
        host = self._request.registry.settings["orcid_host"]
        client_id = self._request.registry.settings["orcid_client_id"]

        state = encode_oauth2_state_param(action, KEY)
        self._request.session[STATE_SESSION_KEY.format(provider="orcid")] = state

        params = {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": self._request.route_url("orcid.oauth.callback"),
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
        renderer="h:templates/notfound.html.jinja2", append_slash=True
    )
    def notfound(self):
        self._request.response.status_int = 401
        return {}


class AccessDeniedError(Exception):
    """The user denied us access to their ORCID record."""


class UserConflictError(Exception):
    """A different Hypothesis user is already connected to this ORCID iD."""


@view_defaults(request_method="GET", route_name="orcid.oauth.callback")
class CallbackViews:
    def __init__(self, request: Request) -> None:
        self._request = request
        self._orcid_client = request.find_service(ORCIDClientService)
        self._user_service = request.find_service(name="user")

    @view_config(is_authenticated=True)
    def callback(self):
        expected_state = self._request.session.pop(
            STATE_SESSION_KEY.format(provider="orcid"), None
        )

        try:
            callback_data = OAuth2RedirectSchema.validate(
                dict(self._request.params), expected_state
            )
        except ValidationError as err:
            if self._request.params.get("error") == "access_denied":
                # The user clicked the deny button on ORCID's page.
                raise AccessDeniedError from err

            # We received an invalid or unexpected redirect from ORCID.
            raise

        decoded_state = decode_oauth2_state_param(callback_data["state"], KEY)

        if decoded_state["action"] == "connect":
            orcid = self._orcid_client.get_orcid(callback_data["code"])

            already_connected_user = self._user_service.fetch_by_identity(
                IdentityProvider.ORCID, orcid
            )

            # Oops, this ORCID iD is already connected to a *different* Hypothesis
            # account.
            if already_connected_user and already_connected_user != self._request.user:
                raise UserConflictError

            if not already_connected_user:
                # This ORCID iD isn't connected to a Hypothesis account yet.
                # Let's go ahead and connect it to the user's account.
                self._orcid_client.add_identity(self._request.user, orcid)

            self._request.session.flash("ORCID iD connected ✓", "success")
            return HTTPFound(location=self._request.route_url("account"))

        raise RuntimeError

    @notfound_view_config(
        renderer="h:templates/notfound.html.jinja2", append_slash=True
    )
    def notfound(self):
        self._request.response.status_int = 401
        return {}

    @exception_view_config(context=ValidationError)
    def invalid(self):
        self._request.session.flash("Received an invalid redirect from ORCID!", "error")
        return HTTPFound(location=self._request.route_url("account"))

    @exception_view_config(context=TokenValidationError)
    def invalid_token(self):
        self._request.session.flash("Received an invalid token from ORCID!", "error")
        return HTTPFound(location=self._request.route_url("account"))

    @exception_view_config(context=AccessDeniedError)
    def denied(self):
        self._request.session.flash("The user clicked the deny button!", "error")
        return HTTPFound(location=self._request.route_url("account"))

    @exception_view_config(context=ExternalRequestError)
    def external_request(self):
        handle_external_request_error(self._request.exception)
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

    report_exception()
