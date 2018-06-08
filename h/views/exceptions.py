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

from h.util.view import handle_exception


@forbidden_view_config(renderer="h:templates/notfound.html.jinja2")
@notfound_view_config(renderer="h:templates/notfound.html.jinja2", append_slash=True)
def notfound(request):
    """Handle a request for an unknown/forbidden resource."""
    request.response.status_int = 404
    return {}


@view_config(
    context=Exception, accept="text/html", renderer="h:templates/5xx.html.jinja2"
)
def error(request):
    """Handle a request for which the handler threw an exception."""
    handle_exception(request)
    return {}
