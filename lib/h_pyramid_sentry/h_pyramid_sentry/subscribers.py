"""A pyramid subscriber to add extra info to retryable events"""
import traceback

from pyramid.events import subscriber
from pyramid_retry import IBeforeRetry
import sentry_sdk


@subscriber(IBeforeRetry)
def add_retryable_error_to_sentry_context(event):
    """
    Add information about a retryable error to the Sentry context.

    If a request raises a retryable error then, if we're not already on this
    request's last retry attempt, pyramid_retry calls this IBeforeRetry
    subscriber function before it retries the request.

    This function adds some information to the Sentry context about the
    retryable error that was raised by the failed attempt at the request.

    If a future retry of this request raises a non-retryable error, or if we
    use up the maximum number of retry attempts, so that we ultimately end up
    sending an error response back to the client, then the information that
    this function adds to the Sentry context will be included in the event that
    is ultimately reported to Sentry.

    This makes debugging errors easier because you can see information about
    previous failed attempts at the request, as well as the usual information
    about the last exception that was raised by the final attempt.

    If a future retry of this request succeeds and we ultimately end up sending
    a successful response back to the client then nothing will be reported to
    Sentry.

    See:

    * https://docs.pylonsproject.org/projects/pyramid-retry/en/latest/#receiving-retry-notifications
    * https://docs.sentry.io/platforms/python/#extra-context
    """
    attempt = event.environ.get("retry.attempt")
    attempts = event.environ.get("retry.attempts")
    exception = event.exception

    if attempt is None or attempts is None:
        return

    # The first attempt is numbered 0. Let's make it more human.
    attempt = attempt + 1

    traceback_str = "".join(
        traceback.format_exception(type(exception), exception, exception.__traceback__)
    )

    # Sentry event variables are limited to 512 characters long, otherwise they
    # get truncated: https://docs.sentry.io/development/sdk-dev/data-handling/
    # We don't want the end of our stack trace to get truncated because the end
    # of a stack trace is the most useful part of it, so truncate the start
    # ourselves instead.
    if len(traceback_str) > 512:
        traceback_str = "..." + traceback_str[-509:]

    with sentry_sdk.configure_scope() as scope:
        scope.set_extra(
            f"Exception from attempt {attempt}/{attempts}",
            repr(exception) or str(exception),
        )
        scope.set_extra(
            f"End of traceback from attempt {attempt}/{attempts}", traceback_str
        )
