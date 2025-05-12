import logging
from urllib.parse import urlencode, urlunparse

import sentry_sdk
from h_pyramid_sentry import report_exception
from pyramid.httpexceptions import HTTPFound
from pyramid.view import exception_view_config, view_config

from h import i18n
from h.models.user_identity import IdentityProvider
from h.schemas.oauth import RetrieveOAuthCallbackSchema
from h.services import ORCIDClientService
from h.services.exceptions import ExternalRequestError

_ = i18n.TranslationString

logger = logging.getLogger(__name__)


@view_config(
    request_method="GET",
    route_name="orcid.oauth.authorize",
)
def authorize(request):
    host = request.registry.settings["orcid_host"]
    client_id = request.registry.settings["orcid_client_id"]
    state = ReadOAuthCallbackData(request).state_param()

    return HTTPFound(
        location=urlunparse(
            (
                "https",
                host,
                "oauth/authorize",
                "",
                urlencode(
                    {
                        "client_id": client_id,
                        "response_type": "code",
                        "redirect_uri": request.route_url("orcid.oauth.callback"),
                        "state": state,
                        "scope": "openid",
                    }
                ),
                "",
            )
        )
    )


@view_config(
    request_method="GET",
    route_name="orcid.oauth.callback",
)
def oauth_redirect(request):
    callback_data = RetrieveOAuthCallbackSchema(request).validate(dict(request.params))

    orcid_client = request.find_service(ORCIDClientService)
    orcid = orcid_client.get_orcid(callback_data["code"])
    user_service = request.find_service(name="user")
    orcid_user = user_service.fetch_by_identity(IdentityProvider.ORCID, orcid)

    # Link ORCID identity to an existing user
    if not orcid_user and request.user:
        orcid_client.add_identity(request.user, orcid)
        return HTTPFound(location=request.route_url("account"))

    logger.error("ORCID oauth redirect flow not supported")
    return HTTPFound(location=request.route_url("index"))


@exception_view_config(
    request_method="GET",
    route_name="orcid.oauth.callback",
    renderer="h:templates/5xx.html.jinja2",
)
@exception_view_config(
    request_method="GET",
    route_name="orcid.oauth.authorize",
    renderer="h:templates/5xx.html.jinja2",
)
def oauth_redirect_error(_request):
    logger.error("ORCID oauth redirect error", exc_info=True)
    return {}


@exception_view_config(context=ExternalRequestError)
def external_request_error(request):
    sentry_sdk.set_context(
        "request",
        {
            "method": request.context.method,
            "url": request.context.url,
            "body": request.context.request_body,
        },
    )
    sentry_sdk.set_context(
        "response",
        {
            "status_code": request.context.status_code,
            "reason": request.context.reason,
            "body": request.context.response_body,
        },
    )
    sentry_sdk.set_context("validation_errors", request.context.validation_errors)

    report_exception()
