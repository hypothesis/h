# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h._compat import urlparse


def match(uri, scopes):
    """
    Return boolean: Does the URI's scope match any of the scopes?

    Return True if the scope of URI is present in the scopes list

    :param uri: URI string in question
    :param scopes: List of scope (URI origin) strings
    """
    scope = uri_scope(uri)
    return scope in scopes


def uri_scope(uri):
    """
    Return the scope for a given URI

    Parse a scope from a URI string. Presently a scope is an origin, so this
    proxies to _parse_origin.
    """
    return _parse_origin(uri)


def _parse_origin(uri):
    """
    Return the origin of a URI or None if empty or invalid.

    Per https://tools.ietf.org/html/rfc6454#section-7 :
    Return ``<scheme> + '://' + <host> + <port>``
    for a URI.

    :param uri: URI string
    """

    if uri is None:
        return None
    parsed = urlparse.urlsplit(uri)
    # netloc contains both host and port
    origin = urlparse.SplitResult(parsed.scheme, parsed.netloc, "", "", "")
    return origin.geturl() or None
