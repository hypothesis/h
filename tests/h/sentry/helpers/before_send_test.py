# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import mock
import pytest

from h.sentry.helpers.before_send import before_send


@pytest.mark.usefixtures("Event", "filters")
class TestBeforeSend(object):
    def test_it_creates_an_Event(self, Event):
        before_send(mock.sentinel.event_dict, mock.sentinel.hint_dict)

        Event.assert_called_once_with(mock.sentinel.event_dict, mock.sentinel.hint_dict)

    def test_it_calls_all_the_filters(self, Event, filters):
        before_send(mock.sentinel.event_dict, mock.sentinel.hint_dict)

        # If you've added a new filter function you should add it to this list.
        filters = [filters.filter_ws4py_error_terminating_connection]

        for filter in filters:
            filter.assert_called_once_with(Event.return_value)

    def test_it_filters_out_the_event_if_a_filter_fails(self, filters):
        filters.filter_ws4py_error_terminating_connection.return_value = False

        result = before_send(mock.sentinel.event_dict, mock.sentinel.hint_dict)

        assert result is None

    def test_it_lets_through_the_event_if_all_filters_pass(self):
        result = before_send(mock.sentinel.event_dict, mock.sentinel.hint_dict)

        assert result == mock.sentinel.event_dict

    @pytest.fixture
    def Event(self, patch):
        return patch("h.sentry.helpers.before_send.Event")

    @pytest.fixture
    def filters(self, patch):
        return patch("h.sentry.helpers.before_send.filters")
