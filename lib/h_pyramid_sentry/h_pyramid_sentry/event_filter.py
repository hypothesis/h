"""An object which filters events"""
import logging

from h_pyramid_sentry.event import Event
from h_pyramid_sentry.exceptions import FilterNotCallableError


class EventFilter:
    """
    A object which contains a list of filter functions and applies
    them to :class:`Event` objects. If the filter returns a truthy value,
    then the event will be suppressed, otherwise it will be passed through.

    This is intended to be used with the Sentry SDK.
    """

    log = logging.getLogger(__name__)
    log_message_prefix = "Filtering out Sentry event"
    log_message_template = f"{log_message_prefix}: %s"

    def __init__(self, filter_functions=None):
        self.filters = []

        if filter_functions is None:
            return

        for filter_function in filter_functions:
            if not callable(filter_function):
                raise FilterNotCallableError(filter_function)

            self.filters.append(filter_function)

    def before_send(self, event_dict, hint_dict):
        """
        Decide whether the given Sentry event should be reported or not.

        Each time an event (for example an uncaught exception or a logged
        error) that would be reported to Sentry happens, ``sentry_sdk`` calls
        this function passing the event first.

        If this function returns ``event_dict`` then the event will be reported
        to Sentry. If this function returns ``None`` the event won't be
        reported.

        See https://docs.sentry.io/error-reporting/configuration/filtering/
        """
        event = Event(event_dict, hint_dict)

        if any(filter_function(event) for filter_function in self.filters):
            self.log.info(self.log_message_template, hint_dict)
            return None

        return event_dict
