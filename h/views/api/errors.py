"""
API exception views.

Views rendered by the web application in response to exceptions thrown within
API views.
"""

from h_api.exceptions import JSONAPIError
from pyramid import httpexceptions
from pyramid.view import forbidden_view_config, notfound_view_config, view_config

from h.i18n import TranslationString as _
from h.util.view import handle_exception, json_view
from h.views.api.config import cors_policy
from h.views.api.decorators import (
    normalize_not_found,
    unauthorized_to_not_found,
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
def oauth_error(context, request):  # pragma: no cover
    """Handle an expected/deliberately thrown OAuth exception."""
    request.response.status_code = context.status_code
    return {"detail": context.detail}


@json_view(context=httpexceptions.HTTPError, decorator=cors_policy)
def api_error(context, request):
    """Handle an expected/deliberately thrown API exception."""
    request.response.status_code = context.status_code
    return {"status": "failure", "reason": context.detail}


@json_view(context=JSONAPIError, path_info="/api/bulk", decorator=cors_policy)
def bulk_api_error(context, request):  # pragma: no cover
    """Handle JSONAPIErrors produced by the Bulk API."""
    request.response.status_code = context.http_status
    return context.as_dict()


@json_view(context=Exception, path_info="/api/", decorator=cors_policy)
def json_error(context, request):  # pragma: no cover
    """Handle an unexpected exception in an API view."""
    handle_exception(request, exception=context)
    message = _(
        "Hypothesis had a problem while handling this request. "
        "Our team has been notified. Please contact support@hypothes.is"
        " if the problem persists."
    )
    return {"status": "failure", "reason": message}
