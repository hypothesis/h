# -*- coding: utf-8 -*-
"""Helpers for the Python 2 to Python 3 transition."""
from __future__ import unicode_literals

import sys

__all__ = (
    "PY2",
    "text_type",
    "string_types",
    "configparser",
    "urlparse",
    "url_quote",
    "url_quote_plus",
    "url_unquote",
    "url_unquote_plus",
    "StringIO",
)

PY2 = sys.version_info[0] == 2

if not PY2:
    text_type = str
    string_types = (str,)
    xrange = range
    unichr = chr
else:
    text_type = unicode  # noqa
    string_types = (str, unicode)  # noqa
    xrange = xrange
    unichr = unichr

try:
    import ConfigParser as configparser
except ImportError:
    import configparser

try:
    from urllib import parse as urlparse

    url_quote = urlparse.quote
    url_quote_plus = urlparse.quote_plus
    url_unquote = urlparse.unquote
    url_unquote_plus = urlparse.unquote_plus
except ImportError:
    import urllib
    import urlparse

    url_quote = urllib.quote
    url_quote_plus = urllib.quote_plus
    url_unquote = urllib.unquote
    url_unquote_plus = urllib.unquote_plus

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


# native() function adapted from Pyramid:
# https://github.com/Pylons/pyramid/blob/a851d05f76edc6bc6bf65269c20eeba7fe726ade/pyramid/compat.py#L78-L95
if PY2:

    def native(s, encoding="latin-1", errors="strict"):
        """
        Return the given string as a Python 2 native string (a byte string).

        If the given string is a unicode string then return it as a byte
        string (Latin 1 encoded by default).

        If the given string is already a byte string (in any encoding) just
        return it unmodified.

        Latin 1 encoding is used by default because that's the encoding used
        for "native" strings in PEP-3333 (the WSGI spec).

        """
        if isinstance(s, unicode):  # noqa
            return s.encode(encoding, errors)
        return s


else:

    def native(s, encoding="latin-1", errors="strict"):
        """
        Return the given string as a Python 3 native string (a unicode string).

        If the given string is a byte string then return it decoded to unicode
        (using Latin 1 by default).

        If the given string is already a unicode string then just return it
        unmodified.

        Latin 1 encoding is used by default because that's the encoding used
        for "native" strings in PEP-3333 (the WSGI spec).

        """
        if isinstance(s, str):
            return s
        return str(s, encoding, errors)
