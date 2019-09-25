# -*- coding: utf-8 -*-
"""
Functions for filtering out events we don't want to report to Sentry.

Each function takes a :class:`h.sentry.helpers.event.Event` argument and
returns ``True`` if the event should be reported to Sentry or ``False`` to
filter it out. Every filter function gets called for every event and if any one
filter returns ``False`` for a given event then the event is not reported.
"""
from __future__ import unicode_literals

from pyramid.threadlocal import get_current_request
from pyramid_retry import is_error_retryable
import ws4py.exc


def filter_ws4py_error_logging(event):
    """Filter out all error messages logged by ws4py."""
    if event.logger == "ws4py":
        return False
    return True


def filter_ws4py_handshake_error(event):
    """
    Filter out ws4py's HandshakeError when no HTTP_UPGRADE header.

    See https://github.com/hypothesis/h/issues/5498
    """
    if isinstance(event.exception, ws4py.exc.HandshakeError):
        if str(event.exception) == "Header HTTP_UPGRADE is not defined":
            return False
    return True


def filter_retryable_error(event):
    """
    Filter exceptions from requests that are going to be retried.

    If a request raises a retryable error, so pyramid_retry automatically
    retries that request, and a subsequent retry succeeds and we end up sending
    a successful response back to the client, then we don't want to report
    anything to Sentry.

    See:

    https://docs.pylonsproject.org/projects/pyramid-retry/en/latest/api.html#pyramid_retry.is_error_retryable
    """
    request = get_current_request()

    if request is None:
        # get_current_request() returns None if we're outside of Pyramid's
        # request context. This happens when sentry-sdk's Pyramid integration
        # catches an exception that Pyramid is going to raise to the WSGI
        # server (Gunicorn, in our case).
        # Always allow these uncaught exceptions to be reported to Sentry:
        return True

    if is_error_retryable(request, event.exception):
        # Don't report the exception to Sentry if the request is going to be
        # re-tried.
        #
        # Note: is_error_retryable() returns *False* if the error is marked as
        # retryable but the request is on its last attempt and is not going to
        # be re-tried again, so if a request fails with a retryable exception
        # on its last attempt (and we send back an error response to the
        # client) that exception will still be reported.
        return False

    return True
