# -*- coding: utf-8 -*-

"""
API exception views.

Views rendered by the web application in response to exceptions thrown within
API views.
"""

from __future__ import unicode_literals

from pyramid.view import forbidden_view_config
from pyramid.view import notfound_view_config

from h.i18n import TranslationString as _  # noqa: N813
from h.exceptions import APIError
from h.schemas import ValidationError
from h.util.view import handle_exception, json_view


# Within the API, render a JSON 403/404 message.
@forbidden_view_config(path_info='/api/', renderer='json')
@notfound_view_config(path_info='/api/', renderer='json')
def api_notfound(request):
    """Handle a request for an unknown/forbidden resource within the API."""
    request.response.status_code = 404
    message = _("Either the resource you requested doesn't exist, or you are "
                "not currently authorized to see it.")
    return {'status': 'failure', 'reason': message}


@json_view(context=APIError)
def api_error(context, request):
    """Handle an expected/deliberately thrown API exception."""
    request.response.status_code = context.status_code
    return {'status': 'failure', 'reason': context.message}


@json_view(context=ValidationError, path_info='/api/')
def api_validation_error(context, request):
    request.response.status_code = 400
    return {'status': 'failure', 'reason': context.message}


@json_view(context=Exception)
def json_error(request):
    """Handle an unexpected exception where the request asked for JSON."""
    handle_exception(request)
    message = _("Uh-oh, something went wrong! We're very sorry, our "
                "application wasn't able to load this page. The team has "
                "been notified and we'll fix it shortly. If the problem "
                "persists or you'd like more information please email "
                "support@hypothes.is with the subject 'Internal Server "
                "Error'.")
    return {'status': 'failure', 'reason': message}
