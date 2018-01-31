# -*- coding: utf-8 -*-
"""Test logging filters."""
from __future__ import unicode_literals

import pytest
import logging
from requests.exceptions import ReadTimeout
from h.search.logging_filters import FilterExceptions


class TestLoggingFilters(object):
    """Test logging filters."""

    def test_filter_bad_level(self):  #pylint: disable=no-self-use
        with pytest.raises(ValueError):
            FilterExceptions((("requests.exceptions.ReadTimeout", "WARNI"),))

    def test_filter_wrong_exception_name(self):  #pylint: disable=no-self-use
        with pytest.raises(ValueError):
            FilterExceptions((("requests.exceptions.Bugga", "WARN"),))

    def test_filter_wrong_module_name(self):  #pylint: disable=no-self-use
        with pytest.raises(ValueError):
            FilterExceptions((("requests.bad.ReadTimeout", "WARN"),))

    def test_filter_no_log(self, logger):  #pylint: disable=no-self-use,redefined-outer-name
        try:
            raise ReadTimeout("this is a test read timeout error")
        except ReadTimeout:
            logger.warn("warning", exc_info=True)
        assert not logger.handlers[0].handler_called, "Didn't filter out log message when it should have!!"

    def test_filter_log_level_mistmatch(self, logger):  #pylint: disable=no-self-use,redefined-outer-name
        try:
            raise ReadTimeout("this is a test read timeout error")
        except ReadTimeout:
            logger.critical("critical", exc_info=True)
        assert logger.handlers[0].handler_called, "Filtered out log message when it shouldn't have!!"

    def test_filter_log_exception_mismatch(self, logger):  #pylint: disable=no-self-use,redefined-outer-name
        try:
            raise Exception("this is a test read timeout error")
        except Exception:
            logger.warn("warning", exc_info=True)
        assert logger.handlers[0].handler_called, "Filtered out log message when it shouldn't have!!"

    def test_filter_no_exc_info(self, logger):  #pylint: disable=no-self-use,redefined-outer-name
        try:
            raise ReadTimeout("this is a test read timeout error")
        except ReadTimeout:
            logger.warn("warning")
        assert logger.handlers[0].handler_called, "Filtered out log message when it shouldn't have!!"


@pytest.fixture
def logger():
    class TestHandler(logging.Handler):
        handler_called = False

        def emit(self, record):
            self.handler_called = True

    log = logging.Logger('test_logger')
    log.addHandler(TestHandler())
    log.addFilter(FilterExceptions((("requests.exceptions.ReadTimeout", "WARNING"),)))
    return log
