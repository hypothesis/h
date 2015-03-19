# -*- coding: utf-8 -*-
import pyramid.events

import h.api_client


def _api_url(request):
    """Return the configured base URL for this app's Hypothesis API instance.

    Returns the value of the h.api_url setting from the config file,
    or if that doesn't exist the "/api" route from the WSGI app (which assumes
    that we're running the app with the "api" feature enabled).

    Always returns the URL _without_ a trailing /, despite what the user might
    have entered in the config file.

    """
    return request.registry.settings.get(
        "h.api_url", request.resource_url(request.root, "api")).rstrip("/")


def api_client(request):
    """Return an api_client.Client instance for this app.

    Configured with this app's configured API base URL.

    """
    return h.api_client.Client(_api_url(request))


@pyramid.events.subscriber(pyramid.events.NewRequest)
def add_api_client(event):
    """Add an API client object to the request.

    This avoids each view that needs it having to initialize an API client
    object itself.

    """
    event.request.set_property(api_client, name="api_client", reify=True)


def includeme(config):
    config.scan(__name__)
