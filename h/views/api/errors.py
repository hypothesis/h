# -*- coding: utf-8 -*-

"""
API exception views.

Views rendered by the web application in response to exceptions thrown within
API views.
"""

from __future__ import unicode_literals

from pyramid.view import forbidden_view_config
from pyramid.view import notfound_view_config
from pyramid.view import view_config
from pyramid import httpexceptions

from h.i18n import TranslationString as _  # noqa: N813
from h.util.view import handle_exception, json_view
from h.views.api.config import cors_policy
from h.views.api.decorators import (
    unauthorized_to_not_found,
    normalize_not_found,
    validate_media_types,
)
from h.views.api.exceptions import OAuthAuthorizeError

# All exception views below need to apply the `cors_policy` decorator for the
# responses to be readable by web applications other than those on the same
# origin as h itself.


# Handle raised 403 and 404 exceptions
@forbidden_view_config(
    path_info="/api/",
    renderer="json",
    decorator=(cors_policy, unauthorized_to_not_found),
)
@notfound_view_config(
    path_info="/api/",
    renderer="json",
    decorator=(cors_policy, normalize_not_found, validate_media_types),
)
def api_notfound(context, request):
    request.response.status_code = context.status_code
    return {"status": "failure", "reason": context.message}


@view_config(
    context=OAuthAuthorizeError, renderer="h:templates/oauth/error.html.jinja2"
)
def oauth_error(context, request):
    """Handle an expected/deliberately thrown OAuth exception."""
    request.response.status_code = context.status_code
    return {"detail": context.detail}


@json_view(context=httpexceptions.HTTPError, decorator=cors_policy)
def api_error(context, request):
    """Handle an expected/deliberately thrown API exception."""
    request.response.status_code = context.status_code
    return {"status": "failure", "reason": context.detail}


@json_view(context=Exception, path_info="/api/", decorator=cors_policy)
def json_error(context, request):
    """Handle an unexpected exception in an API view."""
    handle_exception(request, exception=context)
    message = _(
        "Hypothesis had a problem while handling this request. "
        "Our team has been notified. Please contact support@hypothes.is"
        " if the problem persists."
    )
    return {"status": "failure", "reason": message}
