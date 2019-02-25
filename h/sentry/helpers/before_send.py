# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from h.sentry.helpers.event import Event
from h.sentry.helpers import filters


log = logging.getLogger(__name__)


def before_send(event_dict, hint_dict):
    """
    Decide whether the given Sentry event should be reported or not.

    Each time an event (for example an uncaught exception or a logged error)
    that would be reported to Sentry happens, ``sentry_sdk`` calls this
    function passing the event first.

    If this function returns ``event_dict`` then the event will be reported to
    Sentry. If this function returns ``None`` the event won't be reported.

    See https://docs.sentry.io/error-reporting/configuration/filtering/
    """
    event = Event(event_dict, hint_dict)

    # The list of filters that each event will be passed through.
    # If you add a new filter function you should add it to this list to enable
    # it.
    filter_functions = [
        filters.filter_ws4py_error_logging,
        filters.filter_ws4py_handshake_error,
    ]

    # If every filter returns True then do report the event to Sentry.
    if all(
        [filter_function(event) for filter_function in filter_functions]
    ):  # pragma: no branch
        return event_dict

    # If any one filter returned False then don't report the event to Sentry.
    log.info("Filtering out Sentry event: %s", hint_dict)
    return None
