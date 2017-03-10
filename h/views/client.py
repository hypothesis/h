# -*- coding: utf-8 -*-

"""
Hypothesis client views.

Views which exist either to serve or support the Hypothesis client.
"""

from __future__ import unicode_literals

import json

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from h import session as h_session
from h.auth.tokens import generate_jwt
from h.util.view import json_view
from h import __version__

# Default URL for the client, which points to the latest version of the client
# that was published to npm.
DEFAULT_CLIENT_URL = 'https://cdn.hypothes.is/hypothesis'


def _client_url(request):
    """
    Return the configured URL for the client.
    """
    return request.registry.settings.get('h.client_url', DEFAULT_CLIENT_URL)


@view_config(route_name='sidebar_app',
             renderer='h:templates/app.html.jinja2',
             csp_insecure_optout=True)
def sidebar_app(request, extra=None):
    """
    Return the HTML for the Hypothesis client's sidebar application.

    :param extra: A dict of optional properties specifying link tags and meta
                  attributes to be included on the page.
    """

    settings = request.registry.settings
    ga_client_tracking_id = settings.get('ga_client_tracking_id')
    sentry_public_dsn = settings.get('h.sentry_dsn_client')
    websocket_url = settings.get('h.websocket_url')

    app_config = {
        'apiUrl': request.route_url('api.index'),
        'authDomain': request.auth_domain,
        'release': __version__,
        'serviceUrl': request.route_url('index'),
    }

    if websocket_url:
        app_config.update({
            'websocketUrl': websocket_url,
        })

    if sentry_public_dsn:
        app_config.update({
            'raven': {
                'dsn': sentry_public_dsn,
                'release': __version__
            }
        })

    if ga_client_tracking_id:
        app_config.update({
            'googleAnalytics': ga_client_tracking_id
        })

    ctx = {
        'app_config': json.dumps(app_config),
        'embed_url': request.route_path('embed'),
    }

    if extra is not None:
        ctx.update(extra)

    return ctx


# This view requires credentials (a cookie) so is not currently accessible
# off-origin, unlike the rest of the API. Given that this method of
# authenticating to the API is not intended to remain, this seems like a
# limitation we do not need to lift any time soon.
@view_config(route_name='token', renderer='string', request_method='GET')
def annotator_token(request):
    """
    Return a JWT access token for the given request.

    The token can be used in the Authorization header in subsequent requests to
    the API to authenticate the user identified by the
    request.authenticated_userid of the _current_ request, which may be None.
    """
    return generate_jwt(request, 3600)


@view_config(route_name='embed',
             http_cache=(60 * 5, {'public': True}))
def embed_redirect(request):
    """
    Redirect to the script which loads the Hypothesis client on a page.

    This view provides a fixed URL which redirects to the latest version of the
    client, typically hosted on a CDN.
    """
    return HTTPFound(_client_url(request))


@json_view(route_name='session', http_cache=0)
def session_view(request):
    flash = h_session.pop_flash(request)
    model = h_session.model(request)
    return dict(status='okay', flash=flash, model=model)
