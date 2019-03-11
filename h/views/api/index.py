# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.views.api.config import api_config
from h.views.api.helpers.angular import AngularRouteTemplater
from h.views.api.helpers import links


@api_config(versions=["v1"], route_name="api.index")
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

    return {"links": links.format_nested_links(api_links, "v1", templater)}
