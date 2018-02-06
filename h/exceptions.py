# -*- coding: utf-8 -*-

"""Exceptions raised by the h application."""

from __future__ import unicode_literals

from h.i18n import TranslationString as _  # noqa: N813


class APIError(Exception):

    """Base exception for problems handling API requests."""

    def __init__(self, message, status_code=500):
        self.status_code = status_code
        super(APIError, self).__init__(message)


class ClientUnauthorized(APIError):

    """
    Exception raised if the client credentials provided for an API request
    were missing or invalid.
    """

    def __init__(self):
        message = _('Client credentials are invalid.')
        super(ClientUnauthorized, self).__init__(message, status_code=403)


class OAuthTokenError(APIError):

    """
    Exception raised when an OAuth token request failed.

    This specifically handles OAuth errors which have a type (``message``) and
    a description (``description``).
    """

    def __init__(self, message, type_, status_code=400):
        self.type = type_
        super(OAuthTokenError, self).__init__(message, status_code=status_code)


class PayloadError(APIError):

    """
    Exception raised for API requests made with missing/invalid
    payloads.
    """

    def __init__(self):
        message = _('Expected a valid JSON payload, but none was found!')
        super(PayloadError, self).__init__(message, status_code=400)
