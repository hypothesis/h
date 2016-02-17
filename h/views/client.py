# -*- coding: utf-8 -*-

"""
Application client views.

Views which exist either to serve or support the JavaScript annotation client.
"""

from __future__ import unicode_literals

from pyramid.view import view_config

from h import client
from h import session
from h.util.view import json_view


def render_app(request, extra=None):
    """Render a page that serves a preconfigured annotation client."""
    html = client.render_app_html(
        api_url=request.route_url('api'),
        service_url=request.route_url('index'),
        ga_tracking_id=request.registry.settings.get('ga_tracking_id'),
        sentry_public_dsn=request.sentry.get_public_dsn(),
        webassets_env=request.webassets_env,
        websocket_url=request.registry.settings.get('h.websocket_url'),
        extra=extra)
    request.response.text = html
    return request.response


@view_config(route_name='embed')
def embed(context, request):
    request.response.content_type = b'text/javascript'
    request.response.text = client.render_embed_js(
        webassets_env=request.webassets_env,
        app_html_url=request.resource_url(context, 'app.html'),
        base_url=request.route_url('index'))
    return request.response


@json_view(route_name='session', http_cache=0)
def session_view(request):
    flash = session.pop_flash(request)
    model = session.model(request)
    return dict(status='okay', flash=flash, model=model)


@view_config(route_name='widget')
def widget(context, request):
    return render_app(request)


def includeme(config):
    config.scan(__name__)
