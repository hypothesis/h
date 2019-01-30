# -*- coding: utf-8 -*-
"""
Functions for filtering out events we don't want to report to Sentry.

Each function takes a :class:`h.sentry.helpers.event.Event` argument and
returns ``True`` if the event should be reported to Sentry or ``False`` to
filter it out. Every filter function gets called for every event and if any one
filter returns ``False`` for a given event then the event is not reported.
"""
from __future__ import unicode_literals

import ws4py.exc


def filter_ws4py_error_terminating_connection(event):
    """
    Filter out ws4py's "Error when terminating connection" message.

    Thousands of these get logged every day in production and I don't think
    they're actually a problem.

    See: https://github.com/hypothesis/h/issues/5496
    """
    if event.logger == "ws4py" and event.message.startswith(
        "Error when terminating the connection"
    ):
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
