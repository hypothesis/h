# -*- coding: utf-8 -*-

"""
Hypothesis client views.

Views which exist either to serve or support the Hypothesis client.
"""

from __future__ import unicode_literals

import json
import time

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from h import __version__

# Default URL for the client, which points to the latest version of the client
# that was published to npm.
DEFAULT_CLIENT_URL = "https://cdn.hypothes.is/hypothesis"


def _client_url(request):
    """
    Return the configured URL for the client.
    """
    url = request.registry.settings.get("h.client_url", DEFAULT_CLIENT_URL)

    if request.feature("embed_cachebuster"):
        url += "?cachebuster=" + str(int(time.time()))
    return url


@view_config(
    route_name="sidebar_app",
    renderer="h:templates/app.html.jinja2",
    csp_insecure_optout=True,
)
def sidebar_app(request, extra=None):
    """
    Return the HTML for the Hypothesis client's sidebar application.

    :param extra: A dict of optional properties specifying link tags and meta
                  attributes to be included on the page.
    """

    settings = request.registry.settings
    ga_client_tracking_id = settings.get("ga_client_tracking_id")
    sentry_public_dsn = settings.get("h.sentry_dsn_client")
    websocket_url = settings.get("h.websocket_url")

    app_config = {
        "apiUrl": request.route_url("api.index"),
        "authDomain": request.default_authority,
        "oauthClientId": settings.get("h.client_oauth_id"),
        "release": __version__,
        # The list of origins that the client will respond to cross-origin RPC
        # requests from.
        "rpcAllowedOrigins": settings.get("h.client_rpc_allowed_origins"),
    }

    if websocket_url:
        app_config.update({"websocketUrl": websocket_url})

    if sentry_public_dsn:
        app_config.update({"raven": {"dsn": sentry_public_dsn, "release": __version__}})

    if ga_client_tracking_id:
        app_config.update({"googleAnalytics": ga_client_tracking_id})

    ctx = {
        "app_config": json.dumps(app_config),
        "embed_url": request.route_path("embed"),
    }

    if extra is not None:
        ctx.update(extra)

    return ctx


@view_config(route_name="embed", http_cache=(60 * 5, {"public": True}))
def embed_redirect(request):
    """
    Redirect to the script which loads the Hypothesis client on a page.

    This view provides a fixed URL which redirects to the latest version of the
    client, typically hosted on a CDN.
    """
    return HTTPFound(_client_url(request))
