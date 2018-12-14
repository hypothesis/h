# -*- coding: utf-8 -*-

"""
The query parser which converts our subset of the Apache Lucene syntax and
transforms it into a MultiDict structure that h.search understands.
"""

from __future__ import unicode_literals

from collections import namedtuple

import pyparsing as pp
from webob.multidict import MultiDict

# Enable memoizing of the parsing logic
pp.ParserElement.enablePackrat()

# Named fields we support when querying (e.g. `user:luke`)
named_fields = ["user", "tag", "group", "uri", "url"]

whitespace = set(
    [
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
    ]
)

parser = None
Match = namedtuple("Match", ["key", "value"])


def parse(q):
    """Parse a free text, Lucene-like, query string into a MultiDict.

    "user:luke tag:foobar tag:news hello world" is parsed into::

      {
          "user": "luke",
          "tag": "foobar",
          "tag": "news",
          "any": "hello",
          "any": "world"
      }

    Supported keys for fields are ``user``, ``group``, ``tag``, ``uri``.
    Any other search terms will get the key ``any``.
    """
    parser = _get_parser()
    parse_results = parser.parseString(q)

    # The parser returns all matched strings, even the field names, we use a
    # parse action to turn matches into a key/value pair (Match), but we need
    # to filter out any other matches that the parser returns.
    return MultiDict([m for m in parse_results if isinstance(m, Match)])


def unparse(q):
    """
    Turn a dict-like object into a Lucene-like query string.

    This can be considered the reverse of the :py:func:`h.search.parser.parse`
    function, as it can be used to transform the MultiDict returned from that
    function back into a string query.
    """
    terms = []

    for key, val in q.items():
        if key == "any":
            terms.append(_escape_term(val))
        else:
            terms.append("{key}:{val}".format(key=key, val=_escape_term(val)))

    return " ".join(terms)


def _get_parser():
    global parser
    if parser is None:
        parser = _make_parser()
    return parser


def _make_parser():
    word = pp.CharsNotIn("".join(whitespace))
    word.skipWhitespace = True

    value = pp.MatchFirst(
        [
            pp.dblQuotedString.copy().setParseAction(pp.removeQuotes),
            pp.sglQuotedString.copy().setParseAction(pp.removeQuotes),
            pp.Empty() + pp.CharsNotIn("".join(whitespace)),
        ]
    )

    expressions = []

    for field in named_fields:
        exp = pp.Suppress(
            pp.CaselessLiteral(field) + ":"
        ) + value.copy().setParseAction(_decorate_match(field))
        expressions.append(exp)

    any_ = value.copy().setParseAction(_decorate_match("any"))
    expressions.append(any_)

    return pp.ZeroOrMore(pp.MatchFirst(expressions))


def _decorate_match(key):
    def parse_action_impl(t):
        return Match(key, t[0])

    return parse_action_impl


def _escape_term(term):
    # Only surround with quotes if the term contains whitespace
    if whitespace.intersection(term):
        # Originally double quoted and contained escaped double quotes
        if '\\"' in term:
            return '"' + term + '"'
        # Originally single quoted and contained escaped single quotes
        elif "\\'" in term:
            return "'" + term + "'"
        # Contains unescaped single quotes, so easiest to double quote
        elif "'" in term:
            return '"' + term + '"'
        # None of the above: prefer single quotes
        else:
            return "'" + term + "'"
    return term
