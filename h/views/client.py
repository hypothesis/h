# -*- coding: utf-8 -*-

"""
Application client views.

Views which exist either to serve or support the JavaScript annotation client.
"""

from __future__ import unicode_literals

from pyramid import exceptions
from pyramid import httpexceptions
from pyramid import session
from pyramid.view import view_config

from h import client
from h import session as h_session
from h.api.auth import generate_jwt
from h.util.view import json_view


def render_app(request, extra=None):
    """Render a page that serves a preconfigured annotation client."""
    html = client.render_app_html(
        # FIXME: The '' here is to ensure this has a trailing slash. This seems
        # rather messy, and is inconsistent with the rest of the application's
        # URLs.
        api_url=request.route_url('api.index'),
        service_url=request.route_url('index'),
        ga_tracking_id=request.registry.settings.get('ga_tracking_id'),
        sentry_public_dsn=request.sentry.get_public_dsn(),
        webassets_env=request.webassets_env,
        websocket_url=request.registry.settings.get('h.websocket_url'),
        extra=extra)
    request.response.text = html
    return request.response


# This view requires credentials (a cookie) so is not currently accessible
# off-origin, unlike the rest of the API. Given that this method of
# authenticating to the API is not intended to remain, this seems like a
# limitation we do not need to lift any time soon.
@view_config(route_name='token', renderer='string')
def annotator_token(request):
    """
    Return a JWT access token for the given request.

    The token can be used in the Authorization header in subsequent requests to
    the API to authenticate the user identified by the
    request.authenticated_userid of the _current_ request.
    """
    try:
        session.check_csrf_token(request, token='assertion')
    except exceptions.BadCSRFToken:
        raise httpexceptions.HTTPUnauthorized()

    return generate_jwt(request, 3600)


@view_config(route_name='embed')
def embed(context, request):
    request.response.content_type = b'text/javascript'
    request.response.text = client.render_embed_js(
        webassets_env=request.webassets_env,
        app_html_url=request.route_url('widget'),
        base_url=request.route_url('index'))
    return request.response


@json_view(route_name='session', http_cache=0)
def session_view(request):
    flash = h_session.pop_flash(request)
    model = h_session.model(request)
    return dict(status='okay', flash=flash, model=model)


@view_config(route_name='widget')
def widget(context, request):
    return render_app(request)


def includeme(config):
    config.scan(__name__)
