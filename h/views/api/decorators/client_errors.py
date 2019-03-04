# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from pyramid.httpexceptions import HTTPNotFound

# The default message is not helpful: it's the path
# that failed to match any view. Replace it.
NOT_FOUND_MESSAGE = "Either the resource you requested doesn't exist, or you are not currently authorized to see it."


def unauthorized_to_not_found(wrapped):
    """View decorator to convert all 403 exceptions to 404s"""

    def wrapper(context, request):

        # We convert all 403s to 404s—replace the current context with a 404
        # FIXME: We should be more nuanced about when we do this
        context = HTTPNotFound(NOT_FOUND_MESSAGE)

        response = wrapped(context, request)
        return response

    return wrapper


def not_found_reason(wrapped):
    """View decorator to make 404 error messages more readable"""

    def wrapper(context, request):
        context.message = NOT_FOUND_MESSAGE

        response = wrapped(context, request)
        return response

    return wrapper
