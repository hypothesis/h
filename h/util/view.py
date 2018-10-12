# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid.view import view_config


def handle_exception(request, exception):
    """
    Handle an uncaught exception for the passed request.

    :param request: The Pyramid request which caused the exception.
    :param exception: The exception passed as context to the exception-handling view.
    """
    request.response.status_int = 500
    request.sentry.captureException(exception)
    # In debug mode we should just reraise, so that the exception is caught by
    # the debug toolbar.
    if request.debug:
        raise


def json_view(**settings):
    """A view configuration decorator with JSON defaults."""
    settings.setdefault('accept', 'application/json')
    settings.setdefault('renderer', 'json')
    return view_config(**settings)
