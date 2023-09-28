"""Views serving the homepage and related endpoints."""

from pyramid import httpexceptions
from pyramid.view import view_config


@view_config(route_name="via_redirect", request_method="GET")
def via_redirect(_context, request):  # pragma: no cover
    url = request.params.get("url")

    if url is None:
        raise httpexceptions.HTTPBadRequest('"url" parameter missing')

    via_link = f"https://via.hypothes.is/{url}"
    raise httpexceptions.HTTPFound(location=via_link)


@view_config(route_name="index", request_method="GET")
def index_redirect(_context, request):
    try:
        redirect = request.registry.settings["h.homepage_redirect_url"]
    except KeyError:
        # When the redirect URL isn't explicitly configured, we send people to
        # the main activity stream.
        redirect = request.route_url("activity.search")

    if request.user is not None:
        redirect = request.route_url(
            "activity.user_search", username=request.user.username
        )

    raise httpexceptions.HTTPFound(redirect)
