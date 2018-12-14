# -*- coding: utf-8 -*-

"""Exceptions raised by the h application."""

from __future__ import unicode_literals

from pyramid import httpexceptions

from h.i18n import TranslationString as _  # noqa: N813


class APIError(httpexceptions.HTTPError):

    """A problem handling an API request."""

    def __init__(self, message, status_code=500):
        super(APIError, self).__init__(message, status_code=status_code)


class ConflictError(httpexceptions.HTTPConflict):
    """
    Exception raised if client request represents a duplicate of an
    existing resource.
    """

    def __init__(self, message=_("Conflict")):
        super(ConflictError, self).__init__(message)


class OAuthTokenError(httpexceptions.HTTPUnauthorized):

    """
    Exception raised when an OAuth token request failed.

    This specifically handles OAuth errors which have a type (``message``) and
    a description (``description``).
    """

    def __init__(self, message, type_):
        self.type = type_
        super(OAuthTokenError, self).__init__(message)


class PayloadError(httpexceptions.HTTPBadRequest):

    """
    Exception raised for API requests made with missing/invalid
    payloads.
    """

    def __init__(self):
        message = _("Expected a valid JSON payload, but none was found!")
        super(PayloadError, self).__init__(message)
