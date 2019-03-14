# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h._compat import urlparse


def uri_in_scope(uri, scopes):
    """
    Does the URI match any of the scope patterns?

    Return True if the URI matches one or more patterns in scopes (if the
    URI string begins with any of the scope strings)

    :arg uri: URI string in question
    :arg scopes: List of URIs that define scope
    :type scopes: list(str)
    :rtype: bool
    """
    scope_matches = [scope for scope in scopes if uri.startswith(scope)]

    if len(scope_matches):
        return True
    return False


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
    origin = parse_origin(uri)
    path = _parse_path(uri) or None
    return (origin, path)


def _parse_path(uri):
    """Return the path component of a URI string"""
    if uri is None:
        return None
    parsed = urlparse.urlsplit(uri)
    return parsed[2]


def parse_origin(uri):
    """
    Return the origin of a URI or None if empty or invalid.

    Per https://tools.ietf.org/html/rfc6454#section-7 :
    Return ``<scheme> + '://' + <host> + <port>``
    for a URI.

    This can return None if no valid origin can be extracted from ``uri``

    :param uri: URI string
    :rtype: str or None
    """

    if uri is None:
        return None
    parsed = urlparse.urlsplit(uri)
    # netloc contains both host and port
    origin = urlparse.SplitResult(parsed.scheme, parsed.netloc, "", "", "")
    return origin.geturl() or None
