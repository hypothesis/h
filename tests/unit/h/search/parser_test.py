import string

import pytest
from webob.multidict import MultiDict

from h.search import parser

pytestmark = [
    pytest.mark.xdist_group("elasticsearch"),
    pytest.mark.usefixtures("init_elasticsearch"),
]


@pytest.mark.parametrize(
    "query_in,query_out",
    [
        # user field
        ("user:luke", MultiDict([("user", "luke")])),
        ("user:luke@hypothes.is", MultiDict([("user", "luke@hypothes.is")])),
        ("user:acct:luke@hypothes.is", MultiDict([("user", "acct:luke@hypothes.is")])),
        ("user:luke user:alice", MultiDict([("user", "luke"), ("user", "alice")])),
        ('user:"luke and alice"', MultiDict([("user", "luke and alice")])),
        ('user:"luke"', MultiDict([("user", "luke")])),
        ("USER:luke", MultiDict([("user", "luke")])),
        # tag field
        ("tag:foo", MultiDict([("tag", "foo")])),
        ("tag:foo tag:bar", MultiDict([("tag", "foo"), ("tag", "bar")])),
        ("tag:'foo bar'", MultiDict([("tag", "foo bar")])),
        ('tag:"foo bar"', MultiDict([("tag", "foo bar")])),
        ("tag:'foobar'", MultiDict([("tag", "foobar")])),
        ("Tag:foo", MultiDict([("tag", "foo")])),
        # group field
        ("group:__world__", MultiDict([("group", "__world__")])),
        (
            "group:__world__ group:My-Group",
            MultiDict([("group", "__world__"), ("group", "My-Group")]),
        ),
        ("GrOuP:__world__", MultiDict([("group", "__world__")])),
        # uri field
        ("uri:https://example.com", MultiDict([("uri", "https://example.com")])),
        (
            "uri:urn:x-pdf:hthe-fingerprint",
            MultiDict([("uri", "urn:x-pdf:hthe-fingerprint")]),
        ),
        (
            "uri:https://foo.com uri:http://bar.com",
            MultiDict([("uri", "https://foo.com"), ("uri", "http://bar.com")]),
        ),
        (
            "uri:https://example.com?foo=bar&baz=qux#hello",
            MultiDict([("uri", "https://example.com?foo=bar&baz=qux#hello")]),
        ),
        ("URI:https://example.com", MultiDict([("uri", "https://example.com")])),
        # url field
        ("url:https://example.com", MultiDict([("url", "https://example.com")])),
        (
            "url:urn:x-pdf:hthe-fingerprint",
            MultiDict([("url", "urn:x-pdf:hthe-fingerprint")]),
        ),
        (
            "url:https://foo.com url:http://bar.com",
            MultiDict([("url", "https://foo.com"), ("url", "http://bar.com")]),
        ),
        (
            "url:https://example.com?foo=bar&baz=qux#hello",
            MultiDict([("url", "https://example.com?foo=bar&baz=qux#hello")]),
        ),
        ("URL:https://example.com", MultiDict([("url", "https://example.com")])),
        # any field
        ("foo", MultiDict([("any", "foo")])),
        ("foo bar", MultiDict([("any", "foo"), ("any", "bar")])),
        ('foo "bar baz"', MultiDict([("any", "foo"), ("any", "bar baz")])),
        # unrecognized fields go into any
        ("bogus:hello", MultiDict([("any", "bogus:hello")])),
        # combinations
        (
            "user:luke group:__world__ tag:foobar hello world",
            MultiDict(
                [
                    ("user", "luke"),
                    ("group", "__world__"),
                    ("tag", "foobar"),
                    ("any", "hello"),
                    ("any", "world"),
                ]
            ),
        ),
        (
            "tag:foo bar gRoup:__world__ giraffe",
            MultiDict(
                [
                    ("group", "__world__"),
                    ("tag", "foo"),
                    ("any", "bar"),
                    ("any", "giraffe"),
                ]
            ),
        ),
    ],
)
def test_parse(query_in, query_out):
    assert parser.parse(query_in) == query_out


@pytest.mark.parametrize(
    "query_in,query_out",
    [
        ('""', MultiDict([("any", "")])),
        ("''", MultiDict([("any", "")])),
        ('tag:""', MultiDict([("tag", "")])),
        ('tag:"""', MultiDict([("tag", '"""')])),
        ('"""', MultiDict([("any", '"""')])),
        ("'''", MultiDict([("any", "'''")])),
        ('tag:""""', MultiDict([("tag", '""')])),
        ('""""', MultiDict([("any", '""')])),
        ("''''", MultiDict([("any", "''")])),
        ('tag:"""""', MultiDict([("tag", '"""""')])),
        ('"""""', MultiDict([("any", '"""""')])),
        ("'''''", MultiDict([("any", "'''''")])),
        ('""0', MultiDict([("any", ""), ("any", "0")])),
        ('0""', MultiDict([("any", '0""')])),
        ("''0\"\"", MultiDict([("any", '0""')])),
        ("'0\"", MultiDict([("any", "'0\"")])),
    ],
)
def test_parse_with_odd_quotes_combinations(query_in, query_out):
    assert parser.parse(query_in) == query_out


# Quotes are tested separately, so we cover other non-whitespace chars here.
all_chars_except_quotes = "".join(
    c for c in string.printable if c not in "'\"" and not c.isspace()
)


@pytest.mark.parametrize("field", parser.named_fields)
@pytest.mark.parametrize("value", ["a", "abcd", "123", all_chars_except_quotes])
def test_parse_all_fields_with_non_whitespace_value(field, value):
    result = parser.parse(f"{field}:{value}")
    assert result == MultiDict([(field, value)])


@pytest.mark.parametrize("field", parser.named_fields)
@pytest.mark.parametrize("value", ["", " ", "\t"])
def test_parse_all_fields_with_whitespace_value(field, value):
    result = parser.parse(f"{field}:{value}")
    assert result == MultiDict([("any", f"{field}:")])


@pytest.mark.parametrize(
    "query",
    [
        # Plain dictionary
        {"user": "luke"},
        {"user": "luke", "tag": "foo"},
        # MultiDict
        MultiDict([("user", "luke")]),
        MultiDict([("user", "luke"), ("user", "alice")]),
        # Items containing whitespace
        {"user": "luke duke"},
        {"user": "luke\u00a0duke"},
        MultiDict([("user", "luke duke")]),
        MultiDict([("user", "luke duke"), ("user", "alice and friends")]),
        # Minimally quoted terms including quotes
        {"user": "luke's duke"},
        {"tag": 'and then he said "no way" yes really'},
        # Items which used escape sequences rather than using alternate quotes,
        # e.g. original queries such as:
        #
        #     group:"foo \"hello\" bar"  # noqa: ERA001
        #     tag:'wibble \'giraffe\' bang'  # noqa: ERA001
        {"group": 'foo \\"hello\\" bar'},
        {"tag": "wibble \\'giraffe\\' bang"},
        # Items which contain both single and double quotes
        {"group": 'but "that can\\\'t be", can it?'},
        {"tag": "that is 'one \\\"interesting\\\" way' of looking at it"},
        # 'any' terms
        {"any": "foo"},
        MultiDict([("any", "foo")]),
        MultiDict([("any", "foo"), ("any", "bar baz")]),
        MultiDict([("user", "donkeys"), ("any", "foo"), ("any", "bar baz")]),
    ],
)
def test_unparse(query):
    result = parser.unparse(query)

    # We can't trivially test that the output is exactly what we expect,
    # because of uncertainty in the ordering of keys. Instead, we check that
    # parsing the result gives us an object equal to the original query.
    assert parser.parse(result) == query
