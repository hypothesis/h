"""
Hypothesis client views.

Views which exist either to serve or support the Hypothesis client.
"""

import json
import time

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from h.util.uri import origin, render_url_template

# Default URL for the client, which points to the latest version of the client
# that was published to npm.
DEFAULT_CLIENT_URL = "https://cdn.hypothes.is/hypothesis"


def _client_url(request):
    """Return the configured URL for the client."""
    url = request.registry.settings.get("h.client_url", DEFAULT_CLIENT_URL)
    url = render_url_template(url, example_url=request.url)

    if request.feature("embed_cachebuster"):
        url += "?cachebuster=" + str(int(time.time()))
    return url


@view_config(
    route_name="sidebar_app",
    renderer="h:templates/app.html.jinja2",
    csp_insecure_optout=True,  # This view adds its own custom Content Security Policy
    http_cache=(60 * 5, {"public": True}),
)
@view_config(
    route_name="notebook_app",
    renderer="h:templates/app.html.jinja2",
    csp_insecure_optout=True,  # This view adds its own custom Content Security Policy
    http_cache=(60 * 5, {"public": True}),
)
@view_config(
    route_name="profile_app",
    renderer="h:templates/app.html.jinja2",
    csp_insecure_optout=True,  # This view adds its own custom Content Security Policy
    http_cache=(60 * 5, {"public": True}),
)
def sidebar_app(request, extra=None):
    """
    Return the HTML for the Hypothesis client's sidebar application.

    :param extra: A dict of optional properties specifying link tags and meta
                  attributes to be included on the page.
    """

    settings = request.registry.settings
    sentry_public_dsn = settings.get("h.sentry_dsn_client")

    app_config = {
        "apiUrl": request.route_url("api.index"),
        "authDomain": request.default_authority,
        "oauthClientId": settings.get("h.client_oauth_id"),
        # The list of origins that the client will respond to cross-origin RPC
        # requests from.
        "rpcAllowedOrigins": settings.get("h.client_rpc_allowed_origins"),
    }

    if sentry_public_dsn:  # pragma: no cover
        # `h.sentry_environment` primarily refers to h's Sentry environment,
        # but it also matches the client environment for the embed (dev, qa, prod).
        sentry_environment = settings.get("h.sentry_environment")
        app_config.update(
            {"sentry": {"dsn": sentry_public_dsn, "environment": sentry_environment}}
        )

    ctx = {
        "app_config": json.dumps(app_config),
        "client_url": _client_url(request),
    }

    if extra is not None:  # pragma: no cover
        ctx.update(extra)

    # Add CSP headers to prevent scripts or styles from unexpected locations
    # being loaded in the page. Note that the client sidebar app uses a different
    # CSP than pages that are part of the 'h' website.
    #
    # As well as offering an extra layer of protection against various security
    # risks, this also helps to reduce noise in Sentry reports due to script
    # tags added by e.g. browser extensions.
    client_origin = origin(_client_url(request))

    # nb. Inline styles are currently allowed for the client because LaTeX
    # math rendering using KaTeX relies on them.
    style_src = f"{client_origin} 'unsafe-inline'"

    request.response.headers["Content-Security-Policy"] = (
        f"script-src {client_origin}; style-src {style_src}"
    )

    return ctx


@view_config(route_name="embed", http_cache=(60 * 5, {"public": True}))
def embed_redirect(request):
    """
    Redirect to the script which loads the Hypothesis client on a page.

    This view provides a fixed URL which redirects to the latest version of the
    client, typically hosted on a CDN.
    """
    return HTTPFound(_client_url(request))
