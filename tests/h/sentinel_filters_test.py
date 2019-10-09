import pytest
import ws4py

from unittest import mock

from h import sentry_filters as f
from h_pyramid_sentry.event import Event


class TestFilterWS4PYErrorLogging:
    def test_it_filters_ws4py_logger_events(self):
        event = logger_event("ws4py", "Error when terminating the connection")
        assert f.filter_ws4py_error_logging(event) is True

    def test_it_doesnt_filter_other_logger_events(
            self, unexpected_logger_event):
        assert f.filter_ws4py_error_logging(
            unexpected_logger_event) is False

    def test_it_doesnt_filter_exception_events(
            self, unexpected_exception_event):
        assert f.filter_ws4py_error_logging(
            unexpected_exception_event) is False


class TestFilterWS4PYHandshakeError:
    def test_it_filters_handshake_error_http_upgrade_events(self):
        event = exception_event(
            ws4py.exc.HandshakeError("Header HTTP_UPGRADE is not defined"))

        assert f.filter_ws4py_handshake_error(event) is True

    def test_doesnt_filter_out_other_handshake_errors(self):
        event = exception_event(ws4py.exc.HandshakeError("Some other message"))
        assert f.filter_ws4py_handshake_error(event) is False

    def test_it_doesnt_filter_other_logger_events(
            self, unexpected_logger_event):
        assert f.filter_ws4py_handshake_error(
            unexpected_logger_event) is False

    def test_it_doesnt_filter_exception_events(
            self, unexpected_exception_event):
        assert f.filter_ws4py_handshake_error(
            unexpected_exception_event) is False


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
    """Return a mock :class:`h_pyramid_sentry.event.Event`."""
    return mock.create_autospec(Event, instance=True, spec_set=True)
