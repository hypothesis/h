import pytest
import logging

from unittest.mock import sentinel

from h_pyramid_sentry.event_filter import EventFilter


class TestEventFilter:
    @staticmethod
    def always_filter(*args):
        return True

    @staticmethod
    def never_filter(*args):
        return False

    def test_it_creates_event(self, Event):
        EventFilter.before_send(sentinel.event_dict, sentinel.hint_dict)

        Event.assert_called_once_with(sentinel.event_dict, sentinel.hint_dict)

    def test_adding_filters(self):
        assert not EventFilter.filters_functions

        EventFilter.add_filters([self.always_filter])
        EventFilter.add_filters([self.never_filter])

        assert EventFilter.filters_functions == [self.always_filter, self.never_filter]

    def test_it_filters_when_filter_function_returns_true(self):
        EventFilter.set_filters(
            [
                # Have one that works to ensure we check more
                self.never_filter,
                self.always_filter,
            ]
        )

        assert EventFilter.before_send(sentinel.event_dict, sentinel.hint_dict) is None

    def test_we_do_not_accept_non_callable_objects_as_filters(self):
        with pytest.raises(ValueError):
            EventFilter.set_filters(["not a function"])

    def test_it_passes_error_when_filter_function_returns_false(self):
        EventFilter.set_filters([self.never_filter, self.never_filter])

        assert (
            EventFilter.before_send(sentinel.event_dict, sentinel.hint_dict)
            == sentinel.event_dict
        )

    def test_it_logs_when_an_error_is_filtered(self, caplog):
        caplog.set_level(logging.INFO)

        EventFilter.set_filters([self.always_filter])
        EventFilter.before_send(sentinel.event_dict, sentinel.hint_dict)

        location, level, message = caplog.record_tuples[0]

        assert level == logging.INFO
        assert EventFilter.log_message_prefix in message

    @pytest.fixture
    def Event(self, patch):
        return patch("h_pyramid_sentry.event_filter.Event")
