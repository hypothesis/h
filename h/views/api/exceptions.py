# -*- coding: utf-8 -*-
"""Exceptions raised by the h application."""

from __future__ import unicode_literals

from pyramid import httpexceptions

from h.i18n import TranslationString as _  # noqa: N813


class OAuthAuthorizeError(httpexceptions.HTTPBadRequest):
    """An OAuth authorization request failure."""


class OAuthTokenError(httpexceptions.HTTPUnauthorized):
    """
    An OAuth token request failure.

    Raising an exception of this class causes an error response that has
    a type (``message``) and a description (``description``).
    """

    def __init__(self, detail, type_):
        self.type = type_
        super(OAuthTokenError, self).__init__(detail)


class PayloadError(httpexceptions.HTTPBadRequest):
    """An API request has a missing or invalid payload."""

    def __init__(self):
        detail = _("Expected a valid JSON payload, but none was found!")
        super(PayloadError, self).__init__(detail)
