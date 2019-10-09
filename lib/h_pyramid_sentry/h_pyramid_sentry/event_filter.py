"""An object which filters events"""
import logging

from h_pyramid_sentry.event import Event


class EventFilter:
    """
    A singleton object which contains a list of filter functions and applies
    them to :class:`Event` objects. If the filter returns a truthy value,
    then the event will be suppressed, otherwise it will be passed through.

    This is intended to be used as part of a plugin to Pyramid

    As this is a singleton, the provided filters are global.
    """

    log = logging.getLogger(__name__)
    log_message_prefix = "Filtering out Sentry event"
    log_message_template = f"{log_message_prefix}: %s"
    filters_functions = []

    @classmethod
    def set_filters(cls, filter_functions):
        """
        Set the filters in this object (discarding what was there before)

        :param filter_functions: A list of functions to add
        :raises ValueError: If any of the provided items are not functions
        """
        cls.filters_functions = []
        cls.add_filters(filter_functions)

    @classmethod
    def add_filters(cls, filter_functions):
        """
        Add filters to this object

        :param filter_functions: A list of functions to add
        :raises ValueError: If any of the provided items are not functions
        """
        for filter_function in filter_functions:
            if not callable(filter_function):
                raise ValueError(
                    f"Filter function is not callable: {type(filter_function)}"
                )

            cls.filters_functions.append(filter_function)

    @classmethod
    def before_send(cls, event_dict, hint_dict):
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

        if any(filter_fn(event) for filter_fn in cls.filters_functions):
            cls.log.info(cls.log_message_template, hint_dict)
            return None

        return event_dict
