# -*- coding: utf-8 -*-
"""API view decorators for exception views"""

from __future__ import unicode_literals

from pyramid.httpexceptions import HTTPNotFound, HTTPUnsupportedMediaType

from h.views.api.helpers.media_types import valid_media_types


def unauthorized_to_not_found(wrapped):
    """View decorator to convert all 403 exceptions to 404s"""

    def wrapper(context, request):
        # We convert all 403s to 404s—replace the current context with a 404
        # FIXME: We should be more nuanced about when we do this
        response = wrapped(_standard_not_found(), request)
        return response

    return wrapper


def normalize_not_found(wrapped):
    """View decorator to make 404 error messages more readable"""

    def wrapper(context, request):
        # Replace incoming 404 with one that has a sensible message
        response = wrapped(_standard_not_found(), request)
        return response

    return wrapper


def validate_media_types(wrapped):
    """View decorator to convert certain 4xx errors to 415s"""

    def wrapper(context, request):
        # If Accept has been set
        if request.accept:
            # At least one of the media types in Accept must be known to the app
            if not any([t in valid_media_types() for t in request.accept]):
                # If no Accept media types are known, convert to a 415 error
                context = HTTPUnsupportedMediaType("Unsupported media type")
        response = wrapped(context, request)
        return response

    return wrapper


def _standard_not_found():
    # The default message is not helpful: it's the path
    # that failed to match any view. Replace it.
    return HTTPNotFound(
        "Either the resource you requested doesn't exist, or you are not currently authorized to see it."
    )
