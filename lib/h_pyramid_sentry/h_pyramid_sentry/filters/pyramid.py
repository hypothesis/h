"""Filters specifically for Pyramid"""

# Import is_error_retryable indirectly to make importing from us less
# confusing as we have a very similarly named function
import pyramid_retry

from pyramid.threadlocal import get_current_request


def is_retryable_error(event):
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
        return False

    if pyramid_retry.is_error_retryable(request, event.exception):
        # Don't report the exception to Sentry if the request is going to be
        # re-tried.
        #
        # Note: is_error_retryable() returns *False* if the error is marked as
        # retryable but the request is on its last attempt and is not going to
        # be re-tried again, so if a request fails with a retryable exception
        # on its last attempt (and we send back an error response to the
        # client) that exception will still be reported.
        return True

    return False
