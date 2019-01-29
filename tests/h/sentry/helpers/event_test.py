# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from h.sentry.helpers.event import Event


class TestEvent(object):
    def test_parsing_logger_event(self):
        # The event dict as passed to us by Sentry.
        event_dict = {
            "logger": "test_logger",
            "logentry": {"message": "test_log_message"},
        }

        # The hint dict as passed to us by Sentry.
        hint_dict = {}

        event = Event(event_dict, hint_dict)

        # This is what the Event API looks like for a logger event.
        assert event.event == event_dict
        assert event.hint == hint_dict
        assert event.logger == "test_logger"
        assert event.message == "test_log_message"
        assert event.exception is None

    def test_parsing_exception_event(self):
        # The actual exception object that was raised.
        exception = ValueError("Oops")

        # The event dict as passed to us by Sentry.
        event_dict = {}

        # The hint dict as passed to us by Sentry.
        hint_dict = {"exc_info": (None, exception, None)}

        event = Event(event_dict, hint_dict)

        # This is what the Event API looks like for an exception event.
        assert event.event == event_dict
        assert event.hint == hint_dict
        assert event.logger is None
        assert event.message is None
        assert event.exception == exception
