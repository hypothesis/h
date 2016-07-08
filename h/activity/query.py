# -*- coding: utf-8 -*-

"""
The query parser which converts our subset of the Apache Lucene syntax and
transforms it into a MultiDict structure that h.api.search understands.
"""

from __future__ import unicode_literals

import pyparsing as pp
from webob.multidict import MultiDict

whitespace = set([
    "\u0009",  # character tabulation
    "\u000a",  # line feed
    "\u000b",  # line tabulation
    "\u000c",  # form feed
    "\u000d",  # carriage return
    "\u0020",  # space
    "\u0085",  # next line
    "\u00a0",  # no-break space
    "\u1680",  # ogham space mark
    "\u2000",  # en quad
    "\u2001",  # em quad
    "\u2002",  # en space
    "\u2003",  # em space
    "\u2004",  # three-per-em space
    "\u2005",  # four-per-em space
    "\u2006",  # six-per-em space
    "\u2007",  # figure space
    "\u2008",  # punctuation space
    "\u2009",  # thin space
    "\u200a",  # hair space
    "\u2028",  # line separator
    "\u2029",  # paragraph separator
    "\u202f",  # narrow no-break space
    "\u205f",  # medium mathematical space
    "\u3000",  # ideographic space
])

parser = None


class Match(object):
    """Represents a query segment that matches a specified key."""

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __repr__(self):
        return '<Match key={m.key} value={m.value}>'.format(m=self)


def parse(q):
    """Parse a free text, Lucene-like, query string into a MultiDict.

    "user:luke tag:foobar tag:news hello world" is parsed into:
    ``
    {
        "user": "luke",
        "tag": "foobar",
        "tag": "news",
        "any": "hello",
        "any": "world"
    }
    ``

    Supported keys for fields are ``user``, ``group``, ``tag``, ``uri``.
    Any other search terms will get the key ``any``.
    """
    parser = _get_parser()
    parse_results = parser.parseString(q)

    result = MultiDict()
    for res in parse_results:
        if not isinstance(res, Match):
            continue

        result.add(res.key, res.value)

    return result


def _get_parser():
    global parser
    if parser is None:
        parser = _make_parser()
    return parser


def _make_parser():
    # Enable memoizing of the parsing logic
    pp.ParserElement.enablePackrat()

    word = pp.CharsNotIn(' ')
    word.skipWhitespace = True

    value = pp.MatchFirst([
        pp.quotedString.copy().setParseAction(pp.removeQuotes),
        word
    ])

    expressions = []

    named_fields = ['user', 'tag', 'group', 'uri']
    for field in named_fields:
        exp = (pp.Keyword(field, caseless=True) +
               pp.Suppress(':') +
               value.copy().setParseAction(_decorate_match(field)))
        expressions.append(exp)

    any_ = value.copy().setParseAction(_decorate_match('any'))
    expressions.append(any_)

    return pp.ZeroOrMore(pp.MatchFirst(expressions))


def _decorate_match(key):
    def parse_action_impl(t):
        return Match(key, t[0])
    return parse_action_impl
