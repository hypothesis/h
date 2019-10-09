"""
Functions for filtering out events we don't want to report to Sentry.

This is intended to be passed to h_pyramid_sentry.EventFilter.add_filters
"""
import ws4py.exc


def filter_ws4py_error_logging(event):
    """Filter out all error messages logged by ws4py."""
    return event.logger == "ws4py"


def filter_ws4py_handshake_error(event):
    """
    Filter out ws4py's HandshakeError when no HTTP_UPGRADE header.

    See https://github.com/hypothesis/h/issues/5498
    """
    return (
        isinstance(event.exception, ws4py.exc.HandshakeError)
        and str(event.exception) == "Header HTTP_UPGRADE is not defined"
    )


SENTRY_FILTERS = [filter_ws4py_error_logging, filter_ws4py_handshake_error]
