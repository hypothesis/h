# -*- coding: utf-8 -*-

"""Exceptions raised by :mod:`h.services`."""


class ServiceError(Exception):
    """Base class for all :mod:`h.services` exception classes."""


class ValidationError(ServiceError):
    """A validation problem with a database model."""


class ConflictError(ServiceError):
    """An integrity problem with a database operation."""
