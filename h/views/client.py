# -*- coding: utf-8 -*-

"""
Application client views.

Views which exist either to serve or support the JavaScript annotation client.
"""

from __future__ import unicode_literals

from pyramid.view import view_config

from h import client
from h import session as h_session
from h.auth.tokens import generate_jwt
from h.util.view import json_view


def _client_boot_url(request):
    client_boot_url = None
    if request.feature('use_client_boot_script'):
        client_boot_url = request.route_url('assets_client', subpath='boot.js')
    return client_boot_url


def render_app(request, extra=None):
    """Render a page that serves a preconfigured annotation client."""

    client_boot_url = _client_boot_url(request)
    client_sentry_dsn = request.registry.settings.get('h.client.sentry_dsn')
    html = client.render_app_html(
        assets_env=request.registry['assets_client_env'],
        # FIXME: The '' here is to ensure this has a trailing slash. This seems
        # rather messy, and is inconsistent with the rest of the application's
        # URLs.
        api_url=request.route_url('api.index'),
        service_url=request.route_url('index'),
        sentry_public_dsn=client_sentry_dsn,
        websocket_url=request.registry.settings.get('h.websocket_url'),
        ga_client_tracking_id=request.registry.settings.get('ga_client_tracking_id'),
        extra=extra,
        client_boot_url=client_boot_url)
    request.response.text = html
    return request.response


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
             renderer='h:templates/embed.js.jinja2')
def embed(request):
    request.response.content_type = 'text/javascript'

    return client.embed_context(
        assets_env=request.registry['assets_client_env'],
        app_html_url=request.route_url('widget'),
        base_url=request.route_url('index'),
        client_asset_root=request.route_url('assets_client', subpath=''),
        client_boot_url=_client_boot_url(request))


@json_view(route_name='session', http_cache=0)
def session_view(request):
    flash = h_session.pop_flash(request)
    model = h_session.model(request)
    return dict(status='okay', flash=flash, model=model)


@view_config(route_name='widget')
def widget(context, request):
    """
    Return the HTML for the Hypothesis client's sidebar application.
    """
    return render_app(request)
