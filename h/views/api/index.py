from functools import partial

from h.views.api.config import api_config
from h.views.api.helpers import links as link_helpers
from h.views.api.helpers.url_template import route_url_template


@api_config(
    versions=["v1"],
    route_name="api.index",
    # nb. We assume that the API index document is the same for all users,
    # regardless of authorization.
    http_cache=(60 * 5, {"public": True}),
)
def index(_context, request):
    """
    Return the API descriptor document.

    Clients may use this to discover endpoints for the API.
    """

    api_links = request.registry.api_links["v1"]
    url_template = partial(route_url_template, request)

    return {"links": link_helpers.format_nested_links(api_links, url_template)}


@api_config(
    versions=["v2"],
    route_name="api.index",
    link_name="index",
    # nb. We assume that the API index document is the same for all users,
    # regardless of authorization.
    http_cache=(60 * 5, {"public": True}),
)
def index_v2(_context, request):
    """
    Return the API descriptor document.

    Clients may use this to discover endpoints for the API.
    """

    api_links = request.registry.api_links["v2"]
    url_template = partial(route_url_template, request)

    return {"links": link_helpers.format_nested_links(api_links, url_template)}
