import logging

import pytest
from urllib3.exceptions import ReadTimeoutError

from h.util.logging_filters import ExceptionFilter


class TestExceptionFilter:
    def test_raises_if_invalid_level_name(self):
        with pytest.raises(ValueError):
            ExceptionFilter((("ReadTimeoutError", "WARNI"),))

    def test_specify_level_as_int(self):
        ExceptionFilter((("ReadTimeoutError", logging.WARNING),))

    def test_does_not_log_specified_exceptions(self, logger, read_timeout_exception):
        try:
            raise read_timeout_exception
        except ReadTimeoutError:
            logger.warning("warning", exc_info=True)
        assert not logger.handlers[
            0
        ].handler_called, "Didn't filter out log message when it should have!!"

    def test_does_log_if_log_level_mismatch(self, logger, read_timeout_exception):
        try:
            raise read_timeout_exception
        except ReadTimeoutError:
            logger.critical("critical", exc_info=True)
        assert logger.handlers[
            0
        ].handler_called, "Filtered out log message when it shouldn't have!!"

    def test_does_log_if_exception_mismatch(self, logger):
        try:
            raise ValueError("Not a read timeout")
        except ValueError:
            logger.warning("warning", exc_info=True)
        assert logger.handlers[
            0
        ].handler_called, "Filtered out log message when it shouldn't have!!"

    def test_does_log_if_no_exc_info_is_recorded(self, logger, read_timeout_exception):
        try:
            raise read_timeout_exception
        except ReadTimeoutError:
            logger.warning("warning")
        assert logger.handlers[
            0
        ].handler_called, "Filtered out log message when it shouldn't have!!"

    @pytest.fixture
    def read_timeout_exception(self):
        return ReadTimeoutError(
            pool=None, url="https://example.com", message="Test exception"
        )


@pytest.fixture
def logger():
    class TestHandler(logging.Handler):
        handler_called = False

        def emit(self, record):
            self.handler_called = True

    log = logging.Logger("test_logger")
    log.addHandler(TestHandler())
    log.addFilter(ExceptionFilter((("ReadTimeoutError", "WARNING"),)))
    return log
