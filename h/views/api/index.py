# -*- coding: utf-8 -*-

from h.views.api.config import api_config
from h.views.api.helpers import links as link_helpers
from h.views.api.helpers.angular import AngularRouteTemplater


@api_config(
    versions=["v1"],
    route_name="api.index",
    # nb. We assume that the API index document is the same for all users,
    # regardless of authorization.
    http_cache=(60 * 5, {"public": True}),
)
def index(context, request):
    """Return the API descriptor document.

    Clients may use this to discover endpoints for the API.
    """

    api_links = request.registry.api_links["v1"]

    # We currently need to keep a list of the parameter names we use in our API
    # paths and pass these explicitly into the templater. As and when new
    # parameter names are added, we'll need to add them here, or this view will
    # break (and get caught by the `test_api_index` functional test).
    templater = AngularRouteTemplater(
        request.route_url, params=["id", "pubid", "user", "userid", "username"]
    )

    return {"links": link_helpers.format_nested_links(api_links, templater)}


@api_config(
    versions=["v2"],
    route_name="api.index",
    link_name="index",
    # nb. We assume that the API index document is the same for all users,
    # regardless of authorization.
    http_cache=(60 * 5, {"public": True}),
)
def index_v2(context, request):
    """Return the API descriptor document.

    Clients may use this to discover endpoints for the API.
    """

    api_links = request.registry.api_links["v2"]

    templater = AngularRouteTemplater(
        request.route_url, params=["id", "pubid", "user", "userid", "username"]
    )

    return {"links": link_helpers.format_nested_links(api_links, templater)}
