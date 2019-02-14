# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.views.api.config import api_config, AngularRouteTemplater


@api_config(route_name="api.index")
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

    links = {}
    for link in api_links:
        method_info = {
            "method": link["method"],
            "url": templater.route_template(link["route_name"]),
            "desc": link["description"],
        }
        _set_at_path(links, link["name"].split("."), method_info)

    return {"links": links}


def _set_at_path(dict_, path, value):
    """
    Set the value at a given `path` within a nested `dict`.

    :param dict_: The root `dict` to update
    :param path: List of path components
    :param value: Value to assign
    """
    key = path[0]
    if key not in dict_:
        dict_[key] = {}

    if len(path) == 1:
        dict_[key] = value
    else:
        _set_at_path(dict_[key], path[1:], value)
