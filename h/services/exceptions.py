# -*- coding: utf-8 -*-

"""Exceptions raised by h services."""

from __future__ import unicode_literals


class ServiceError(Exception):

    """Base exception for problems in services."""

    pass


class ValidationError(ServiceError):

    """Exception class for handling validation problems in models"""

    pass


class ConflictError(ServiceError):

    """Exception class for handling integrity problems with database operations"""

    pass
