# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
from hypothesis import strategies as st
from hypothesis import given
from webob.multidict import MultiDict

from h.activity import query


@pytest.mark.parametrize("query_in,query_out", [
    # user field
    ('user:luke', MultiDict([('user', 'luke')])),
    ('user:luke@hypothes.is', MultiDict([('user', 'luke@hypothes.is')])),
    ('user:acct:luke@hypothes.is', MultiDict([('user', 'acct:luke@hypothes.is')])),
    ('user:luke user:alice', MultiDict([('user', 'luke'), ('user', 'alice')])),
    ('user:"luke and alice"', MultiDict([('user', 'luke and alice')])),
    ('user:"luke"', MultiDict([('user', 'luke')])),
    ('USER:luke', MultiDict([('user', 'luke')])),


    # tag field
    ('tag:foo', MultiDict([('tag', 'foo')])),
    ('tag:foo tag:bar', MultiDict([('tag', 'foo'), ('tag', 'bar')])),
    ('tag:\'foo bar\'', MultiDict([('tag', 'foo bar')])),
    ('tag:"foo bar"', MultiDict([('tag', 'foo bar')])),
    ('tag:\'foobar\'', MultiDict([('tag', 'foobar')])),
    ('Tag:foo', MultiDict([('tag', 'foo')])),

    # group field
    ('group:__world__', MultiDict([('group', '__world__')])),
    ('group:__world__ group:My-Group', MultiDict([('group', '__world__'), ('group', 'My-Group')])),
    ('GrOuP:__world__', MultiDict([('group', '__world__')])),

    # uri field
    ('uri:https://example.com', MultiDict([('uri', 'https://example.com')])),
    ('uri:urn:x-pdf:hthe-fingerprint', MultiDict([('uri', 'urn:x-pdf:hthe-fingerprint')])),
    ('uri:https://foo.com uri:http://bar.com', MultiDict([('uri', 'https://foo.com'), ('uri', 'http://bar.com')])),
    ('uri:https://example.com?foo=bar&baz=qux#hello', MultiDict([('uri', 'https://example.com?foo=bar&baz=qux#hello')])),
    ('URI:https://example.com', MultiDict([('uri', 'https://example.com')])),

    # any field
    ('foo', MultiDict([('any', 'foo')])),
    ('foo bar', MultiDict([('any', 'foo'), ('any', 'bar')])),
    ('foo "bar baz"', MultiDict([('any', 'foo'), ('any', 'bar baz')])),

    # unrecognized fields go into any
    ('bogus:hello', MultiDict([('any', 'bogus:hello')])),

    # combinations
    ('user:luke group:__world__ tag:foobar hello world', MultiDict([
        ('user', 'luke'),
        ('group', '__world__'),
        ('tag', 'foobar'),
        ('any', 'hello'),
        ('any', 'world'),
    ])),
    ('tag:foo bar gRoup:__world__ giraffe', MultiDict([
        ('group', '__world__'),
        ('tag', 'foo'),
        ('any', 'bar'),
        ('any', 'giraffe'),
    ])),
])
def test_parse(query_in, query_out):
    assert query.parse(query_in) == query_out


@pytest.mark.parametrize("query_in,query_out", [
    ('""', MultiDict([('any', '')])),
    ("''", MultiDict([('any', "")])),
    ('tag:""', MultiDict([('tag', '')])),
    ('tag:"""', MultiDict([('tag', '"""')])),
    ('"""', MultiDict([('any', '"""')])),
    ("'''", MultiDict([('any', "'''")])),
    ('tag:""""', MultiDict([('tag', '""')])),
    ('""""', MultiDict([('any', '""')])),
    ("''''", MultiDict([('any', "''")])),
    ('tag:"""""', MultiDict([('tag', '"""""')])),
    ('"""""', MultiDict([('any', '"""""')])),
    ("'''''", MultiDict([('any', "'''''")])),
    ('""0', MultiDict([('any', ''), ('any', '0')])),
    ('0""', MultiDict([('any', '0""')])),
    ('\'\'0""', MultiDict([('any', '0""')])),
    ('\'0"', MultiDict([('any', '\'0"')])),
])
def test_parse_with_odd_quotes_combinations(query_in, query_out):
    assert query.parse(query_in) == query_out


@given(st.text())
@pytest.mark.fuzz
def test_parse_always_return_a_multidict(text):
    """Given any string input, output should always be a MultiDict."""
    result = query.parse(text)
    assert isinstance(result, MultiDict)


# Combinations of strings containing any number of quotes are already tested
# separately.
char_blacklist = query.whitespace.union(set('\'"'))
nonwhitespace_chars = st.characters(blacklist_characters=char_blacklist)
nonwhitespace_text = st.text(alphabet=nonwhitespace_chars, min_size=1)


@given(nonwhitespace_text)
@pytest.mark.fuzz
def test_parse_with_any_nonwhitespace_text(text):
    result = query.parse(text)
    assert result.get('any') == text
