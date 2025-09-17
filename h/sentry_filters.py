"""Functions for filtering out events and log messages we don't want to report to Sentry."""

import ws4py.exc
from sentry_sdk.types import Hint, Log


def sentry_before_send_log(log: Log, _hint: Hint) -> Log | None:
    """Filter out log messages that we don't want to send to Sentry Logs."""

    if log.get("attributes", {}).get("logger.name") == "gunicorn.access":
        return None

    return log


def is_ws4py_error_logging(event):
    """Filter out all error messages logged by ws4py."""
    return event.logger == "ws4py"


def is_ws4py_handshake_error(event):
    """
    Filter out ws4py's HandshakeError when no HTTP_UPGRADE header.

    See https://github.com/hypothesis/h/issues/5498
    """
    return (
        isinstance(event.exception, ws4py.exc.HandshakeError)
        and str(event.exception) == "Header HTTP_UPGRADE is not defined"
    )


# These are intended to be passed to h_pyramid_sentry.EventFilter.add_filters
SENTRY_ERROR_FILTERS = [is_ws4py_error_logging, is_ws4py_handshake_error]
