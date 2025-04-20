from urllib.parse import urlencode, urlunparse

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config


@view_config(
    request_method="GET",
    route_name="orcid.oauth.authorize",
    # permission=Permission.API,  # noqa: ERA001
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
                        "redirect_uri": request.route_url("orcid.oauth.callback"),
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
    # permission=Permission.API,  # noqa: ERA001
    # schema=OAuthCallbackSchema,  # noqa: ERA001
)
def oauth_redirect(request):
    request.find_service(name="orcid_client").get_orcid(request.params["code"])
    return HTTPFound(location=request.route_url("index"))
