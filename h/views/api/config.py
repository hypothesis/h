import venusian

from h.views.api import API_VERSION_DEFAULT, API_VERSIONS
from h.views.api.decorators.response import version_media_type_header
from h.views.api.helpers import cors, links
from h.views.api.helpers.media_types import media_type_for_version

#: Decorator that adds CORS headers to API responses.
#:
#: This decorator enables web applications not running on the same domain as h
#: to make API requests and read the responses.
#:
#: For standard API views the decorator is automatically applied by the
#: ``api_config`` decorator.
#:
#: Exception views need to independently apply this policy because any response
#: headers set during standard request processing are discarded if an exception
#: occurs and an exception view is invoked to generate the response instead.
cors_policy = cors.policy(
    allow_headers=(
        "Authorization",
        "Content-Type",
        "Hypothesis-Client-Version",
        "X-Client-Id",
    ),
    allow_methods=("HEAD", "GET", "PATCH", "POST", "PUT", "DELETE"),
)


def add_api_view(
    config,
    view,
    versions,
    link_name=None,
    description=None,
    enable_preflight=True,
    subtype="json",
    **settings
):

    """
    Add a view configuration for an API view.

    This configuration takes care of some common tasks for configuring
    API views:

    * It registers the view with Pyramid using some appropriate defaults for
      API method views, e.g. JSON and CORs support. As part of this, it also
      configures views to respond to requests for different versions of
      the API, via Accept header negotiation.
    * If ``link_name`` is present, the view will be registered as one of the
      available "links" that are returned by the ``api.index`` route for its
      version(s).

    :param config:
    :type config: :class:`pyramid.config.Configurator`
    :param view: The view callable
    :param versions: API versions this view supports. Each entry must be one of
                     the versions defined in :py:const:`h.views.api.API_VERSIONS`
    :type versions: list[string] or None
    :param str link_name: Dotted path of the metadata for this route in the output
                          of the `api.index` view
    :param str description: Description of the view to use in `api.index`
    :param bool enable_preflight: If ```True``, add support for CORS preflight
                                  requests for this view. If ``True``, a
                                  `route_name` must be specified.
    :param dict settings: Arguments to pass on to ``config.add_view``
    """
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


def api_config(versions, link_name=None, description=None, **settings):
    """
    A view configuration decorator for API views.

    This is similar to Pyramid's `view_config` except that it uses
    `add_api_view` to register the view instead of `context.add_view`.
    """

    def callback(context, name, ob):
        add_api_view(
            context.config,
            view=ob,
            versions=versions,
            link_name=link_name,
            description=description,
            **settings
        )

    def wrapper(wrapped):
        info = venusian.attach(wrapped, callback, category="pyramid")

        # Support use as a class method decorator.
        # Taken from Pyramid's `view_config` decorator implementation.
        if info.scope == "class":
            if settings.get("attr") is None:
                settings["attr"] = wrapped.__name__

        return wrapped

    return wrapper
