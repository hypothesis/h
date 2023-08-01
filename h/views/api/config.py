from typing import List

import venusian
from pyramid.config import Configurator

from h.views.api import API_VERSION_DEFAULT, API_VERSIONS
from h.views.api.decorators.response import version_media_type_header
from h.views.api.helpers import cors, links
from h.views.api.helpers.media_types import media_type_for_version

# Decorator that adds CORS headers to API responses.
#
# This decorator enables web applications not running on the same domain as h
# to make API requests and read the responses.
#
# For standard API views the decorator is automatically applied by the
# `api_config` decorator.
#
# Exception views need to independently apply this policy because any response
# headers set during standard request processing are discarded if an exception
# occurs and an exception view is invoked to generate the response instead.
cors_policy = cors.policy(
    allow_headers=(
        "Authorization",
        "Content-Type",
        "Hypothesis-Client-Version",
        "X-Client-Id",
    ),
    allow_methods=("HEAD", "GET", "PATCH", "POST", "PUT", "DELETE"),
)


def api_config(
    versions: List[str],
    link_name: str = None,
    description: str = None,
    enable_preflight: bool = True,
    subtype: str = "json",
    **settings
):
    """
    Decorate a method to add view configuration for an API view.

    This configuration takes care of some common tasks for configuring
    API views:

    * It registers the view with Pyramid using some appropriate defaults for
      API method views, e.g. JSON and CORs support. As part of this, it also
      configures views to respond to requests for different versions of
      the API, via Accept header negotiation.
    * If `link_name` is present, the view will be registered as one of the
      available "links" that are returned by the `api.index` route for its
      version(s).

    :param versions: API versions this view supports. Each entry must be one of
        the versions defined in `h.views.api.API_VERSIONS`
    :param link_name: Dotted path of the metadata for this route in the output
        of the `api.index` view
    :param description: Description of the view to use in `api.index`
    :param enable_preflight: Add support for CORS preflight requests for this
        view. This requires a `route_name` in settings
    :param subtype: The JSON subtype being used in the accept MIME type
    :param settings: kwargs to pass on to `config.add_view`
    """

    def callback(context, _name, view):
        # This callback is not executed right away, and only takes effect
        # when a venusian scan is triggered over the code.
        _add_api_view(
            context.config,
            view=view,
            versions=versions,
            link_name=link_name,
            description=description,
            enable_preflight=enable_preflight,
            subtype=subtype,
            **settings
        )

    def wrapper(wrapped):
        # Register our decorator with venusian to be applied later
        info = venusian.attach(wrapped, callback, category="pyramid")

        # Set `attr` as required for class methods as views:
        # https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/viewconfig.html#non-predicate-arguments
        # Taken from Pyramid's `view_config` decorator implementation.

        # This works because the above callback forms a closure around
        # `settings`, but has not yet been executed. As we hold a reference to
        # `settings` we can still modify it before the call is made
        if info.scope == "class":  # pylint: disable=no-member
            if settings.get("attr") is None:
                settings["attr"] = wrapped.__name__

        return wrapped

    return wrapper


def _add_api_view(  # pylint: disable=too-many-arguments
    config: Configurator,
    view: callable,
    versions: List[str],
    link_name: str = None,
    description: str = None,
    enable_preflight: bool = True,
    subtype: str = "json",
    **settings
):
    settings.setdefault("renderer", "json")
    settings.setdefault("decorator", (cors_policy, version_media_type_header(subtype)))

    if link_name:
        link = links.ServiceLink(
            name=link_name,
            route_name=settings.get("route_name"),
            method=settings.get("request_method", "GET"),
            description=description,
        )

        links.register_link(link, versions, config.registry)

    if API_VERSION_DEFAULT in versions:
        # If this view claims to support the default API version, register it
        # with the default (application/json) media-type accept handler
        settings.setdefault("accept", "application/json")
        config.add_view(view=view, **settings)

    for version in versions:
        if version not in API_VERSIONS:
            raise ValueError(
                "API Configuration Error: Unrecognized API version " + version
            )

        # config.add_view only allows one, string value for `accept`, so we
        # have to re-invoke it to add additional accept headers
        settings["accept"] = media_type_for_version(version, subtype=subtype)
        config.add_view(view=view, **settings)

    if enable_preflight:
        cors.add_preflight_view(config, settings["route_name"], cors_policy)
