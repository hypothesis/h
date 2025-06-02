import logging
from urllib.parse import urlencode, urlunparse

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

from h import i18n
from h.models.user_identity import IdentityProvider
from h.schemas import ValidationError
from h.schemas.oauth import RetrieveOAuthCallbackSchema
from h.services import ORCIDClientService
from h.services.exceptions import ExternalRequestError
from h.services.jwt import TokenValidationError

_ = i18n.TranslationString

logger = logging.getLogger(__name__)


@view_defaults(request_method="GET", route_name="orcid.oauth.authorize")
class AuthorizeViews:
    def __init__(self, request: Request) -> None:
        self._request = request

    @view_config(is_authenticated=True)
    def authorize(self):
        host = self._request.registry.settings["orcid_host"]
        client_id = self._request.registry.settings["orcid_client_id"]
        state = RetrieveOAuthCallbackSchema(self._request).state_param()

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
    """The user denied us access to their ORCID account."""


class UserConflictError(Exception):
    """A different Hypothesis user is already connected to this ORCID."""


@view_defaults(request_method="GET", route_name="orcid.oauth.callback")
class CallbackViews:
    def __init__(self, request: Request) -> None:
        self._request = request
        self._orcid_client = request.find_service(ORCIDClientService)
        self._user_service = request.find_service(name="user")

    @view_config(is_authenticated=True)
    def callback(self):
        try:
            callback_data = RetrieveOAuthCallbackSchema(self._request).validate(
                dict(self._request.params)
            )
        except ValidationError as err:
            if self._request.params.get("error") == "access_denied":
                # The user clicked the deny button on ORCID's page.
                raise AccessDeniedError from err

            # We received an invalid or unexpected redirect from ORCID.
            raise

        orcid = self._orcid_client.get_orcid(callback_data["code"])

        already_connected_user = self._user_service.fetch_by_identity(
            IdentityProvider.ORCID, orcid
        )

        # Oops, this ORCID is already connected to a *different* Hypothesis
        # account.
        if already_connected_user and already_connected_user != self._request.user:
            raise UserConflictError

        if not already_connected_user:
            # This ORCID isn't connected to a Hypothesis account yet.
            # Let's go ahead and connect it to the user's account.
            self._orcid_client.add_identity(self._request.user, orcid)

        self._request.session.flash("ORCID connected ✓", "success")
        return HTTPFound(location=self._request.route_url("account"))

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
            "A different Hypothesis user is already connected to this ORCID!", "error"
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
