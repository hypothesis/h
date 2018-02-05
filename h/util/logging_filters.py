# -*- coding: utf-8 -*-
"""Logging Filters."""

import logging


# logging levels from https://docs.python.org/2/library/logging.html#logging-levels
LEVELS = {"CRITICAL": 50,
          "ERROR": 40,
          "WARNING": 30,
          "INFO": 20,
          "DEBUG": 10,
          "NOTSET": 0}


class ExceptionFilter(logging.Filter):
    """Filter out the specified exceptions with specified logging level."""

    def __init__(self, ignore_exceptions):
        """
        Configure filtering out of the specified exceptions with specified logging level.

        ignore_exceptions: a tuple of tuples ((exception type, loglevel))
                           example: (("requests.exceptions.ReadTimeout", "WARNING"),)
        """
        super(ExceptionFilter, self).__init__()

        # build decoder dict where both string and int map to int logging level
        logging_levels = {val: val for val in LEVELS.values()}
        logging_levels.update(LEVELS)

        self._ignore_exceptions = []
        for (exc_type, exc_level) in ignore_exceptions:
            exception_idx = exc_type.rfind('.')
            module, exception = exc_type[:exception_idx], exc_type[exception_idx+1:]
            try:
                self._ignore_exceptions.append((logging_levels[exc_level],
                                                getattr(__import__(module), exception)))
            except KeyError:
                raise ValueError("""The logging level provided ({})
                                 is invalid. Valid options: {}"""
                                 .format(exc_level, logging_levels.keys()))
            except (ImportError, AttributeError):
                raise ValueError('The exception path does not exist ({}.{}).'
                                 .format(module, exception))

    def filter(self, record):
        """Filter out the specified exceptions with specified logging level."""
        if record.exc_info:
            for filter_level, filter_exc in self._ignore_exceptions:
                if record.exc_info[0] is filter_exc and record.levelno == filter_level:
                    return False
        return True
