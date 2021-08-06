"""
Application exception views.

Views rendered by the web application in response to exceptions thrown within
views.
"""

from pyramid.view import forbidden_view_config, notfound_view_config, view_config

from h.i18n import TranslationString as _
from h.util.view import handle_exception, json_view


@forbidden_view_config(renderer="h:templates/notfound.html.jinja2")
@notfound_view_config(renderer="h:templates/notfound.html.jinja2", append_slash=True)
def notfound(request):
    """Handle a request for an unknown/forbidden resource."""
    request.response.status_int = 404
    return {}


@view_config(
    context=Exception, accept="text/html", renderer="h:templates/5xx.html.jinja2"
)
def error(context, request):
    """Handle a request for which the handler threw an exception."""
    handle_exception(request, exception=context)
    return {}


@json_view(context=Exception)
def json_error(context, request):
    """Handle an unexpected exception where the request asked for JSON."""
    handle_exception(request, exception=context)
    message = _(
        "Hypothesis had a problem while handling this request. "
        "Our team has been notified. Please contact support@hypothes.is"
        " if the problem persists."
    )
    return {"status": "failure", "reason": message}
