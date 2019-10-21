# -*- coding: utf-8 -*-

import sys

from pyramid.view import view_config


# Test seam. Patching `sys.exc_info` directly causes problems with pytest.
def _exc_info():
    return sys.exc_info()


def handle_exception(request, exception):
    """
    Handle an uncaught exception for the passed request.

    :param request: The Pyramid request which caused the exception.
    :param exception: The exception passed as context to the exception-handling view.
    """
    request.response.status_int = 500


def json_view(**settings):
    """A view configuration decorator with JSON defaults."""
    settings.setdefault("accept", "application/json")
    settings.setdefault("renderer", "json")
    return view_config(**settings)


def render_url_template(url_template, request):
    """
    Replace placeholders in a URL with elements of the current request's URL.

    This function is primarily used in development to support creating
    absolute links to h or other Hypothesis services which work when h is
    accessed from the same system (where the h dev server is "localhost:<port>")
    or a different device (when the h dev server is "machine-name.local:<port>").
    """
    url = url_template
    url = url.replace("{current_host}", request.domain)
    url = url.replace("{current_scheme}", request.scheme)
    return url
