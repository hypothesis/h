# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import mock
import pytest

import ws4py

from h.sentry.helpers import filters
from h.sentry.helpers.event import Event


class TestFilterWS4PYErrorLogging(object):
    def test_it_filters_ws4py_logger_events(self):
        event = logger_event("ws4py", "Error when terminating the connection")
        assert filters.filter_ws4py_error_logging(event) is False

    def test_it_doesnt_filter_other_logger_events(self, unexpected_logger_event):
        assert filters.filter_ws4py_error_logging(unexpected_logger_event) is True

    def test_it_doesnt_filter_exception_events(self, unexpected_exception_event):
        assert filters.filter_ws4py_error_logging(unexpected_exception_event) is True


class TestFilterWS4PYHandshakeError(object):
    def test_it_filters_HandshakeError_HTTP_UPGRADE_events(self):
        event = exception_event(
            ws4py.exc.HandshakeError("Header HTTP_UPGRADE is not defined")
        )
        assert filters.filter_ws4py_handshake_error(event) is False

    def test_doesnt_filter_out_other_HandshakeErrors(self):
        event = exception_event(ws4py.exc.HandshakeError("Some other message"))
        assert filters.filter_ws4py_handshake_error(event) is True

    def test_it_doesnt_filter_other_logger_events(self, unexpected_logger_event):
        assert filters.filter_ws4py_handshake_error(unexpected_logger_event) is True

    def test_it_doesnt_filter_exception_events(self, unexpected_exception_event):
        assert filters.filter_ws4py_handshake_error(unexpected_exception_event) is True


@pytest.fixture
def unexpected_logger_event():
    """Return an unexpected logger event that no filter should stop."""
    return logger_event("unexpected_logger", "unexpected_message")


@pytest.fixture
def unexpected_exception_event():
    """Return an unexpected exception event that no filter should stop."""
    return exception_event(ValueError("Unexpected!"))


def logger_event(logger, message):
    """
    Return a logger event with the given logger name and message.

    Return a mock :class:`h.sentry.helpers.event.Event` of the kind that's
    created when some code calls logger.error().
    """
    event = _event()
    event.logger = logger
    event.message = message
    return event


def exception_event(exception):
    """
    Return an exception event for the given exception object.

    Return a mock :class:`h.sentry.helpers.event.Event` of the kind that's
    created when some code raises an exception.
    """
    event = _event()
    event.exception = exception
    return event


def _event():
    """Return a mock :class:`h.sentry.helpers.event.Event`."""
    return mock.create_autospec(Event, instance=True, spec_set=True)
