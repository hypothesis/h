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


# TODO: This concept no longer makes sense with more granular scoping. There is
# no equivalent 1:1 uri <-> scope relationship. Remove this function soon.
def uri_scope(uri):
    """
    Return the scope for a given URI

    Parse a scope from a URI string. Presently a scope is an origin, so this
    proxies to _parse_origin.
    """
    return _parse_origin(uri)


def uri_to_scope(uri):
    """
    Return a tuple representing the origin and path of a URI

    :arg uri: The URI from which to derive scope
    :type uri: str
    :rtype: tuple(str, str or None)
    """
    # A URL with no origin component will result in a `None` value for
    # origin, while a URL with no path component will result in an empty
    # string for path.
    origin = _parse_origin(uri)
    path = _parse_path(uri) or None
    return (origin, path)


def _parse_path(uri):
    """Return the path component of a URI string"""
    if uri is None:
        return None
    parsed = urlparse.urlsplit(uri)
    return parsed[2]


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
