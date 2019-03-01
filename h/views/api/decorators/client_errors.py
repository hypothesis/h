# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from pyramid.httpexceptions import HTTPForbidden, HTTPNotFound


def client_error_decorator(wrapped):
    """
    Decorate client (HTTP 4xx) exception views

    This decorator makes sure that the context ultimately passed to the wrapped
    exception view is the right kind of HTTP exception and has the right
    kind of message/details.

    The exception view is passed an instance of a descendent of
    :class:`pyramid.httpexceptions.HTTPError` object as
    its context. We replace or modify the exception raised by Pyramid in
    these cases:

    * If the current value of ``request.accept`` is not a known/valid media type.
      Pyramid will raise a :class:`pyramid.httpexceptions.HTTPNotFound`
      in these cases, but we want to respond with a more useful
      :class:`pyramid.httpexceptions.HTTPUnsupportedMediaType` (HTTP 415)
      instead. (STILL TODO)
    * If the supplied context is a :class:`pyramid.httpexceptions.HTTPForbidden`:
      we currently squelch these to avoid leaking the existence of resources.
      Replace ``context`` with a :class:`pyramid.httpexceptions.HTTPNotFound`

    In addition, Pyramid sets the ``detail`` and ``message`` attributes on
    both :class:`pyramid.httpexceptions.HTTPNotFound` and
    :class:`pyramid.httpexceptions.HTTPNotFound` to less-than-great defaults,
    so we set a custom message.
    """

    def wrapper(context, request):

        # If we're dealing with a 403, substitute with a 404 instead
        # FIXME: We should be more nuanced about when we do this
        if isinstance(context, HTTPForbidden):
            context = HTTPNotFound()

        if isinstance(context, HTTPNotFound):
            # The default message is not helpful: it's the path
            # that failed to match any view. Replace it.
            context.message = "Either the resource you requested doesn't exist, or you are not currently authorized to see it."

        response = wrapped(context, request)
        return response

    return wrapper
