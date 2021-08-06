"""Exceptions raised by the h application."""

from pyramid import httpexceptions

from h.i18n import TranslationString as _


class OAuthAuthorizeError(  # pylint: disable=too-many-ancestors
    httpexceptions.HTTPBadRequest
):
    """An OAuth authorization request failure."""


class OAuthTokenError(
    httpexceptions.HTTPUnauthorized
):  # pylint: disable=too-many-ancestors
    """
    An OAuth token request failure.

    Raising an exception of this class causes an error response that has
    a type (``message``) and a description (``description``).
    """

    def __init__(self, detail, type_):
        self.type = type_
        super().__init__(detail)


class PayloadError(httpexceptions.HTTPBadRequest):  # pylint: disable=too-many-ancestors
    """An API request has a missing or invalid payload."""

    def __init__(self):
        detail = _("Expected a valid JSON payload, but none was found!")
        super().__init__(detail)
