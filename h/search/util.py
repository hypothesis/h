# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re
from h._compat import urlparse


def wildcard_uri_is_valid(wildcard_uri):
    """
    Return True if uri contains wildcards in appropriate places, return False otherwise.

    *'s and _'s are not permitted in the scheme or netloc aka:
        scheme://netloc/path;parameters?query#fragment.

    If a wildcard is near the begining of a url, elasticsearch will find a large portion of the
    annotations because it is based on luncene which searches from left to right. In order to
    avoid the performance implications of having such a large initial search space, wildcards are
    not allowed in the begining of the url.
    """
    if "*" not in wildcard_uri and "_" not in wildcard_uri:
        return False

    # Note: according to the URL spec _'s are allowed in the domain so this may be
    # something that needs to be supported at a later date.
    normalized_uri = urlparse.urlparse(wildcard_uri)
    if (
        not normalized_uri.scheme
        or "*" in normalized_uri.netloc
        or "_" in normalized_uri.netloc
    ):
        return False

    return True


def add_default_scheme(uri):
    """
    In order to not prepend an extra http:// in cases where
    there may be wildcard characters in the scheme, add _ and *
    to the list of valid scheme characters.
    For example: ht*://example.com w/o allowing wildcards
        would be http://ht*//example.com which is intuitively wrong.
    Note: This will not add a scheme to server:port uri's.
    """
    # See https://tools.ietf.org/html/rfc3986#section-3.1
    uri_scheme_pattern = "[a-zA-Z_/*][a-zA-Z0-9+-._/*]*:"

    if re.match(uri_scheme_pattern, uri):
        return uri

    return "http://" + uri
