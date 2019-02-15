from __future__ import unicode_literals
import venusian

from h.views.api.helpers import cors


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
    allow_headers=("Authorization", "Content-Type", "X-Client-Id"),
    allow_methods=("HEAD", "GET", "PATCH", "POST", "PUT", "DELETE"),
)


def add_api_view(
    config, view, link_name=None, description=None, enable_preflight=True, **settings
):

    """
    Add a view configuration for an API view.

    This adds a new view using `config.add_view` with appropriate defaults for
    API methods (JSON in & out, CORS support). Additionally if `link_name` is
    specified it adds the view to the list of views returned by the `api.index`
    route.

    :param config: The Pyramid `Configurator`
    :param view: The view callable
    :param link_name: Dotted path of the metadata for this route in the output
                      of the `api.index` view
    :param description: Description of the view to use in the `api.index` view
    :param enable_preflight: If `True` add support for CORS preflight requests
                             for this view. If `True`, a `route_name` must be
                             specified.
    :param settings: Arguments to pass on to `config.add_view`
    """

    # Get the HTTP method for use in the API links metadata
    primary_method = settings.get("request_method", "GET")
    if isinstance(primary_method, tuple):
        # If the view matches multiple methods, assume the first one is
        # preferred
        primary_method = primary_method[0]

    settings.setdefault("accept", "application/json")
    settings.setdefault("renderer", "json")
    settings.setdefault("decorator", cors_policy)

    if link_name:
        link = {
            "name": link_name,
            "method": primary_method,
            "route_name": settings.get("route_name"),
            "description": description,
        }

        registry = config.registry
        if not hasattr(registry, "api_links"):
            registry.api_links = []
        registry.api_links.append(link)

    config.add_view(view=view, **settings)
    if enable_preflight:
        cors.add_preflight_view(config, settings["route_name"], cors_policy)


def api_config(link_name=None, description=None, **settings):
    """
    A view configuration decorator for API views.

    This is similar to Pyramid's `view_config` except that it uses
    `add_api_view` to register the view instead of `context.add_view`.
    """

    def callback(context, name, ob):
        add_api_view(
            context.config,
            view=ob,
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
