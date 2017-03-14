# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid.view import view_config

from h.util import cors

cors_policy = cors.policy(
    allow_headers=(
        'Authorization',
        'Content-Type',
    ),
    allow_methods=('HEAD', 'GET', 'POST', 'PUT', 'DELETE'),
    allow_preflight=True)


def handle_exception(request):
    """Handle an uncaught exception for the passed request."""
    request.response.status_int = 500
    request.sentry.captureException()
    # In debug mode we should just reraise, so that the exception is caught by
    # the debug toolbar.
    if request.debug:
        raise


def json_view(**settings):
    """A view configuration decorator with JSON defaults."""
    settings.setdefault('accept', 'application/json')
    settings.setdefault('renderer', 'json')
    return view_config(**settings)


def cors_json_view(**settings):
    """
    A view configuration decorator with JSON defaults and CORS.

    CORS with Authorization and Content-Type headers.
    """
    settings.setdefault('decorator', cors_policy)

    request_method = settings.get('request_method', ())
    if not isinstance(request_method, tuple):
        request_method = (request_method,)
    if len(request_method) == 0:
        request_method = ('DELETE', 'GET', 'HEAD', 'POST', 'PUT',)
    settings['request_method'] = request_method + ('OPTIONS',)

    return json_view(**settings)
