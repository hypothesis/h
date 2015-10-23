# -*- coding: utf-8 -*-

import collections


def auth_token(handler, registry):
    """
    A tween that copies the value of the Annotator token header into the the
    HTTP Authorization header with the Bearer token type.
    """

    def tween(request):
        token = request.headers.get('X-Annotator-Auth-Token')
        if token is not None:
            request.authorization = ('Bearer', token)
        return handler(request)

    return tween


def conditional_http_tween_factory(handler, registry):
    """A tween that sets up conditional response handling for some requests."""
    def conditional_http_tween(request):
        response = handler(request)

        # If the Last-Modified header has been set, we want to enable the
        # conditional response processing.
        if response.last_modified is not None:
            response.conditional_response = True

        # We want to only enable the conditional machinery if either we were
        # given an explicit ETag header by the view...
        if response.etag is not None:
            response.conditional_response = True
            return response

        # ...or we have a buffered response and can generate the ETag header
        # ourself. We only do this for GET or HEAD requests that result in a
        # status code of 200. The subtleties of doing it correctly in other
        # cases don't bear thinking about (at the moment).
        have_buffered_response = (isinstance(response.app_iter,
                                             collections.Sequence) and
                                  len(response.app_iter) == 1)
        cacheable = (request.method in {"GET", "HEAD"} and
                     response.status_code == 200)
        if have_buffered_response and cacheable:
            response.conditional_response = True
            response.md5_etag()

        return response
    return conditional_http_tween


def csrf_tween_factory(handler, registry):
    """A tween that sets a 'XSRF-TOKEN' cookie."""

    def csrf_tween(request):
        response = handler(request)

        # NB: the session does not necessarily supply __len__.
        session_is_empty = len(request.session.keys()) == 0

        # Ignore an empty session.
        if request.session.new and session_is_empty:
            return response

        csrft = request.session.get_csrf_token()

        if request.cookies.get('XSRF-TOKEN') != csrft:
            response.set_cookie('XSRF-TOKEN', csrft)

        return response

    return csrf_tween
