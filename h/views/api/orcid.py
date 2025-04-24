import logging
from datetime import UTC, datetime
from urllib.parse import urlencode, urlunparse

from pyramid import security
from pyramid.httpexceptions import HTTPFound
from pyramid.view import exception_view_config, view_config

from h.accounts.events import LoginEvent
from h.models.user_identity import IdentityProvider
from h.schemas.oauth import ReadOAuthCallbackSchema
from h.services import ORCIDClientService

logger = logging.getLogger(__name__)


@view_config(
    request_method="GET",
    route_name="orcid.oauth.authorize",
)
def authorize(request):
    host = request.registry.settings["orcid_host"]
    client_id = request.registry.settings["orcid_client_id"]
    state = ReadOAuthCallbackSchema(request).state_param()

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
                        "redirect_uri": "http://localhost.is:5000/orcid/callback",
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
    callback_data = ReadOAuthCallbackSchema(request).validate(dict(request.params))

    orcid_client = request.find_service(ORCIDClientService)
    orcid = orcid_client.get_orcid(callback_data["code"])
    user_service = request.find_service(name="user")
    orcid_user = user_service.fetch_by_identity(IdentityProvider.ORCID, orcid)

    # Sign up new user with ORCID identity
    if not orcid_user and not request.user:
        request.session["pending_orcid"] = orcid
        return HTTPFound(location=request.route_url("signup"))

    # Link ORCID identity to existing user
    if not orcid_user and request.user:
        orcid_client.add_identity(request.user, orcid)
        return HTTPFound(location=request.route_url("account"))

    # Login existing user with ORCID identity
    headers = {}
    if orcid_user and not request.user:
        orcid_user.last_login_date = datetime.now(UTC)
        request.registry.notify(LoginEvent(request, orcid_user))
        headers = security.remember(request, orcid_user.userid)

    return HTTPFound(location=request.route_url("index"), headers=headers)


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
