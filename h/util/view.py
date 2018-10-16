# -*- coding: utf-8 -*-

from __future__ import unicode_literals

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

    # There are two code paths here depending on whether this is the most recent
    # exception in the current thread. If it is, we can let Raven capture
    # the details under Python 2 + 3. If not, we need to construct the
    # exc_info tuple manually and the stacktrace is only available in Python 3.
    last_exc_info = _exc_info()
    if exception is last_exc_info[1]:
        request.sentry.captureException()
    else:
        # `__traceback__` is a Python 3-only property.
        traceback = getattr(exception, '__traceback__', None)
        exc_info = (type(exception), exception, traceback)
        request.sentry.captureException(exc_info)

    # In debug mode we should just reraise, so that the exception is caught by
    # the debug toolbar.
    if request.debug:
        raise


def json_view(**settings):
    """A view configuration decorator with JSON defaults."""
    settings.setdefault('accept', 'application/json')
    settings.setdefault('renderer', 'json')
    return view_config(**settings)
