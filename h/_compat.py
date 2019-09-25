# -*- coding: utf-8 -*-
"""Helpers for the Python 2 to Python 3 transition."""
from __future__ import unicode_literals

from urllib import parse as urlparse

__all__ = (
    "text_type",
    "string_types",
    "urlparse",
    "url_quote",
    "url_quote_plus",
    "url_unquote",
    "url_unquote_plus",
)

text_type = str
string_types = (str,)
unichr = chr

url_quote = urlparse.quote
url_quote_plus = urlparse.quote_plus
url_unquote = urlparse.unquote
url_unquote_plus = urlparse.unquote_plus


# native() function adapted from Pyramid:
# https://github.com/Pylons/pyramid/blob/a851d05f76edc6bc6bf65269c20eeba7fe726ade/pyramid/compat.py#L78-L95
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
