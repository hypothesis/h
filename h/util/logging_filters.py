# -*- coding: utf-8 -*-
"""Logging Filters."""
from __future__ import unicode_literals

import logging


# logging levels from https://docs.python.org/2/library/logging.html#logging-levels
LEVELS = {
    "CRITICAL": 50,
    "ERROR": 40,
    "WARNING": 30,
    "INFO": 20,
    "DEBUG": 10,
    "NOTSET": 0,
}


class ExceptionFilter(logging.Filter):
    """Filter out the specified exceptions with specified logging level."""

    def __init__(self, ignore_exceptions):
        """
        Configure filtering out of the specified exceptions with specified logging level.
        Note if there are multiple exceptions that have the same name this will filter
        out all exceptions with that name.

        ignore_exceptions: a tuple of tuples ((exception name, loglevel))
                           example: (("ReadTimeout", "WARNING"),)
        """
        super(ExceptionFilter, self).__init__()

        # build decoder dict where both string and int map to int logging level
        logging_levels = {val: val for val in LEVELS.values()}
        logging_levels.update(LEVELS)

        self._ignore_exceptions = []
        for (exc_name, exc_level) in ignore_exceptions:
            try:
                self._ignore_exceptions.append((logging_levels[exc_level], exc_name))
            except KeyError:
                raise ValueError(
                    """The logging level provided ({})
                                 is invalid. Valid options: {}""".format(
                        exc_level, logging_levels.keys()
                    )
                )

    def filter(self, record):
        """Filter out the specified exceptions with specified logging level."""
        if record.exc_info:
            for filter_level, filter_exc in self._ignore_exceptions:
                if (
                    record.exc_info[0].__name__ == filter_exc
                    and record.levelno == filter_level
                ):
                    return False
        return True
