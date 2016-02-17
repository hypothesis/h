# -*- coding: utf-8 -*-

"""
Application exception views.

Views rendered by the web application in response to exceptions thrown within
views.
"""

from __future__ import unicode_literals

from pyramid.view import forbidden_view_config
from pyramid.view import notfound_view_config
from pyramid.view import view_config

from h import i18n
from h.util.view import json_view

_ = i18n.TranslationString


@forbidden_view_config(renderer='h:templates/notfound.html.jinja2')
@notfound_view_config(renderer='h:templates/notfound.html.jinja2')
def notfound(context, request):
    request.response.status_int = 404
    return {}


@view_config(context=Exception,
             accept='text/html',
             renderer='h:templates/5xx.html.jinja2')
def error(context, request):
    """Display an error message."""
    _handle_exc(request)
    return {}


@json_view(context=Exception)
def json_error(context, request):
    """"Return a JSON-formatted error message."""
    _handle_exc(request)
    return {"reason": _(
        "Uh-oh, something went wrong! We're very sorry, our "
        "application wasn't able to load this page. The team has been "
        "notified and we'll fix it shortly. If the problem persists or you'd "
        "like more information please email support@hypothes.is with the "
        "subject 'Internal Server Error'.")}


def includeme(config):
    config.scan(__name__)


def _handle_exc(request):
    request.response.status_int = 500
    request.sentry.captureException()
    # In debug mode we should just reraise, so that the exception is caught by
    # the debug toolbar.
    if request.debug:
        raise
