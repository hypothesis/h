# -*- coding: utf-8 -*-
from unittest import mock

import pytest
import ws4py

from h.sentry.helpers import filters
from h.sentry.helpers.event import Event


class TestFilterWS4PYErrorLogging:
    def test_it_filters_ws4py_logger_events(self):
        event = logger_event("ws4py", "Error when terminating the connection")
        assert filters.filter_ws4py_error_logging(event) is False

    def test_it_doesnt_filter_other_logger_events(self, unexpected_logger_event):
        assert filters.filter_ws4py_error_logging(unexpected_logger_event) is True

    def test_it_doesnt_filter_exception_events(self, unexpected_exception_event):
        assert filters.filter_ws4py_error_logging(unexpected_exception_event) is True


class TestFilterWS4PYHandshakeError:
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


class TestFilterRetryableError:
    def test_it_doesnt_filter_non_retryable_errors(self, event):
        assert filters.filter_retryable_error(event) is True

    def test_it_checks_whether_the_error_is_retryable(
        self, event, is_error_retryable, pyramid_request
    ):
        filters.filter_retryable_error(event)

        is_error_retryable.assert_called_once_with(pyramid_request, event.exception)

    def test_it_doesnt_filter_uncaught_errors(
        self, event, get_current_request, is_error_retryable
    ):
        get_current_request.return_value = None

        assert filters.filter_retryable_error(event) is True
        is_error_retryable.assert_not_called()

    def test_it_filters_retryable_errors(self, event, is_error_retryable):
        is_error_retryable.return_value = True

        assert filters.filter_retryable_error(event) is False

    @pytest.fixture
    def event(self):
        event = mock.create_autospec(Event, instance=True, spec_set=True)
        event.exception = RuntimeError("Something went wrong")
        return event

    @pytest.fixture(autouse=True)
    def get_current_request(self, patch, pyramid_request):
        get_current_request = patch("h.sentry.helpers.filters.get_current_request")
        get_current_request.return_value = pyramid_request
        return get_current_request

    @pytest.fixture(autouse=True)
    def is_error_retryable(self, patch):
        is_error_retryable = patch("h.sentry.helpers.filters.is_error_retryable")
        is_error_retryable.return_value = False
        return is_error_retryable


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
