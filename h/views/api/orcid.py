from datetime import UTC, datetime
from urllib.parse import urlencode, urlunparse

from markupsafe import Markup
from pyramid import security
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from h.accounts.events import LoginEvent
from h.i18n import TranslationString
from h.models.user_identity import IdentityProvider
from h.services import ORCIDClientService


@view_config(
    request_method="GET",
    route_name="orcid.oauth.authorize",
)
def authorize(request):
    host = request.registry.settings["orcid_host"]
    client_id = request.registry.settings["orcid_client_id"]
    # state = OAuthCallbackSchema(request).state_param()  # noqa: ERA001

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
                        # "state": state,  # noqa: ERA001
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
    # schema=OAuthCallbackSchema,  # noqa: ERA001
)
def oauth_redirect(request):
    orcid_client = request.find_service(ORCIDClientService)
    orcid = orcid_client.get_orcid(request.params["code"])
    user_service = request.find_service(name="user")
    orcid_user = user_service.fetch_by_identity(IdentityProvider.ORCID, orcid)

    # Sign up new user with ORCID identity
    if not orcid_user and not request.user:
        return HTTPFound(location=request.route_url("signup", _query={"orcid": orcid}))

    # Link ORCID identity to existing user
    if not orcid_user and request.user:
        orcid_client.add_identity(request.user, orcid)

    # Login existing user with ORCID identity
    headers = {}
    if orcid_user and not request.user:
        orcid_user.last_login_date = datetime.now(UTC)
        request.registry.notify(LoginEvent(request, orcid_user))
        headers = security.remember(request, orcid_user.userid)

    return HTTPFound(location=request.route_url("index"), headers=headers)
