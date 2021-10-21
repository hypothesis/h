# pylint: disable=unused-argument
import logging
from collections.abc import Sequence

import importlib_resources
from pyramid import httpexceptions
from pyramid.util import DottedNameResolver

from h.util.redirects import lookup as lookup_redirects
from h.util.redirects import parse as parse_redirects

log = logging.getLogger(__name__)
resolver = DottedNameResolver(None)


def conditional_http_tween_factory(handler, registry):
    """Set up conditional response handling for some requests."""

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
        have_buffered_response = (
            isinstance(response.app_iter, Sequence) and len(response.app_iter) == 1
        )
        cacheable = request.method in {"GET", "HEAD"} and response.status_code == 200
        if have_buffered_response and cacheable:
            response.conditional_response = True
            response.md5_etag()

        return response

    return conditional_http_tween


def invalid_path_tween_factory(handler, registry):
    def invalid_path_tween(request):
        # Due to a bug in WebOb accessing request.path (or request.path_info
        # etc) will raise UnicodeDecodeError if the requested path doesn't
        # decode with UTF-8, and this will result in a 500 Server Error from
        # our app.
        #
        # Detect this situation and send a 400 Bad Request instead.
        #
        # See:
        # https://github.com/Pylons/webob/issues/115
        # https://github.com/hypothesis/h/issues/4915
        try:
            request.path
        except UnicodeDecodeError:
            return httpexceptions.HTTPBadRequest()

        return handler(request)

    return invalid_path_tween


def redirect_tween_factory(handler, registry, redirects=None):
    if redirects is None:
        # N.B. If we fail to load or parse the redirects file, the application
        # will fail to boot. This is deliberate: a missing/corrupt redirects
        # file should result in a healthcheck failure.

        with (importlib_resources.files("h") / "redirects").open(
            encoding="utf-8"
        ) as handle:
            redirects = parse_redirects(handle)

    def redirect_tween(request):
        url = lookup_redirects(redirects, request)
        if url is not None:
            return httpexceptions.HTTPMovedPermanently(location=url)
        return handler(request)

    return redirect_tween


def security_header_tween_factory(handler, registry):
    """Add security-related headers to every response."""

    def security_header_tween(request):
        resp = handler(request)
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Referrer-Policy
        #
        # Browsers should respect the last value they recognise from this
        # list, thus browsers that don't support
        # strict-origin-when-cross-origin will fall back to
        # origin-when-cross-origin.
        resp.headers[
            "Referrer-Policy"
        ] = "origin-when-cross-origin, strict-origin-when-cross-origin"
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-XSS-Protection
        resp.headers["X-XSS-Protection"] = "1; mode=block"
        return resp

    return security_header_tween


def cache_header_tween_factory(handler, registry):
    """Set default caching headers on responses depending on the content type."""

    def cache_header_tween(request):
        resp = handler(request)

        # Require revalidation before using any cached API responses.
        if "application/json" in resp.headers.get("Content-Type", []):
            resp.headers.setdefault("Cache-Control", "no-cache")

        return resp

    return cache_header_tween


def rollback_db_session_on_exception_factory(handler, registry):
    """
    Catch exceptions and rolls the database back.

    Thas way it can be reliably used again regardless of what exception caused the error.
    """

    # Intended to be run before excview_tween_factory here:
    # https://docs.pylonsproject.org/projects/pyramid/en/1.10-branch/_modules/pyramid/tweens.html#excview_tween_factory
    def rollback_db_session_on_exception(request):
        try:
            return handler(request)

        except Exception:
            request.db.rollback()
            # Pass off to excview_tween to start exception view processing
            raise

    return rollback_db_session_on_exception
