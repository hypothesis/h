# -*- coding: utf-8 -*-
"""Helpers for the Python 2 to Python 3 transition."""
from __future__ import unicode_literals

import sys

__all__ = (
    'PY2',

    'text_type',
    'string_types',

    'configparser',

    'urlparse',
    'url_quote',
    'url_quote_plus',
    'url_unquote',
    'url_unquote_plus',

    'StringIO',
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
