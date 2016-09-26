# -*- coding: utf-8 -*-

"""Exceptions raised by the h application."""

from __future__ import unicode_literals


# N.B. This class **only** covers exceptions thrown by API code provided by
# the h package. memex code has its own base APIError class.
class APIError(Exception):

    """Base exception for problems handling API requests."""

    def __init__(self, message, status_code=500):
        self.status_code = status_code
        super(APIError, self).__init__(message)
