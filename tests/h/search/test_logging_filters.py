# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import logging
import sys
from h.search.logging_filters import FilterExceptions
from requests.exceptions import ReadTimeout


class TestLoggingFilters:
    def test_filter_bad_input_level(self):
        with pytest.raises(ValueError):
            FilterExceptions((("requests.exceptions.ReadTimeout","WARNI"),))

    def test_filter_bad_input_exc_path_exc_name(self):
        with pytest.raises(ValueError):
            FilterExceptions((("requests.exceptions.Bugga","WARN"),))

    def test_filter_bad_input_exc_path_mod(self):
        with pytest.raises(ValueError):
            FilterExceptions((("requests.bad.ReadTimeout","WARN"),))

    def test_filter_no_log(self, logger):
        try:
            raise ReadTimeout("this is a test read timeout error")
        except:
            logger.warn("warning", exc_info=True)
        assert not logger.handlers[0].handler_called, "Didn't filter out log message when it should have!!"

    def test_filter_do_log_level_mistmatch(self, logger):
        try:
            raise ReadTimeout("this is a test read timeout error")
        except:
            logger.critical("critical", exc_info=True)
        assert logger.handlers[0].handler_called, "Filtered out log message when it shouldn't have!!"

    def test_filter_do_log_exception_mismatch(self, logger):
        try:
            raise Exception("this is a test read timeout error")
        except:
            logger.warn("warning", exc_info=True)
        assert logger.handlers[0].handler_called, "Filtered out log message when it shouldn't have!!"

    def test_filter_no_exc_info(self, logger):
        try:
            raise ReadTimeout("this is a test read timeout error")
        except:
            logger.warn("warning")
        assert logger.handlers[0].handler_called, "Filtered out log message when it shouldn't have!!"


@pytest.fixture
def logger():
    class TestHandler(logging.Handler):
        handler_called = False

        def emit(self, record):
            self.handler_called = True

    logger = logging.Logger('test_logger')
    logger.addHandler(TestHandler())
    logger.addFilter(FilterExceptions((("requests.exceptions.ReadTimeout","WARNING"),)))
    return logger
