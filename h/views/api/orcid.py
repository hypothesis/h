from urllib.parse import urlencode, urlunparse

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

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
    orcid_client.add_identity(request.user, orcid)
    return HTTPFound(location=request.route_url("index"))
