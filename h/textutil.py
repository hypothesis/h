# -*- coding: utf-8 -*-

from __future__ import unicode_literals

# We use the new "regex" package (slated eventually to replace stdlib's "re"
# package) in order to get access to unicode matching mode.
import regex as re
from unidecode import unidecode

PUNCT_OR_WS = re.compile(r'[\p{Punctuation}\p{Whitespace}]+')


def slugify(text, delim='-'):
    """Generate an ASCII-only slug from unicode input."""
    result = []
    for word in PUNCT_OR_WS.split(text):
        result.extend(unidecode(word).split())
    return unicode(delim.join(r.lower() for r in result))
