# -*- coding: utf-8 -*-

import mock
import pytest
from hypothesis import strategies as st
from hypothesis import given
from webob import multidict

from h.api.search import query

MISSING = object()

OFFSET_DEFAULT = 0
LIMIT_DEFAULT = 20
LIMIT_MAX = 200


@pytest.mark.parametrize('offset,from_', [
    # defaults to OFFSET_DEFAULT
    (MISSING, OFFSET_DEFAULT),
    # straightforward pass-through
    (7, 7),
    (42, 42),
    # string values should be converted
    ("23", 23),
    ("82", 82),
    # invalid values should be ignored and the default should be returned
    ("foo",  OFFSET_DEFAULT),
    ("",     OFFSET_DEFAULT),
    ("   ",  OFFSET_DEFAULT),
    ("-23",  OFFSET_DEFAULT),
    ("32.7", OFFSET_DEFAULT),
])
def test_builder_offset(offset, from_):
    builder = query.Builder()

    if offset is MISSING:
        q = builder.build({})
    else:
        q = builder.build({"offset": offset})

    assert q["from"] == from_


@given(st.text())
@pytest.mark.fuzz
def test_builder_limit_output_within_bounds(text):
    """Given any string input, output should be in the allowed range."""
    builder = query.Builder()

    q = builder.build({"limit": text})

    assert isinstance(q["size"], int)
    assert 0 <= q["size"] <= LIMIT_MAX


@given(st.integers())
@pytest.mark.fuzz
def test_builder_limit_output_within_bounds_int_input(lim):
    """Given any integer input, output should be in the allowed range."""
    builder = query.Builder()

    q = builder.build({"limit": str(lim)})

    assert isinstance(q["size"], int)
    assert 0 <= q["size"] <= LIMIT_MAX


@given(st.integers(min_value=0, max_value=LIMIT_MAX))
@pytest.mark.fuzz
def test_builder_limit_matches_input(lim):
    """Given an integer in the allowed range, it should be passed through."""
    builder = query.Builder()

    q = builder.build({"limit": str(lim)})

    assert q["size"] == lim


def test_builder_limit_missing():
    builder = query.Builder()

    q = builder.build({})

    assert q["size"] == LIMIT_DEFAULT


def test_builder_sort_is_by_updated():
    """Sort defaults to "updated"."""
    builder = query.Builder()

    q = builder.build({})

    sort = q["sort"]
    assert len(sort) == 1
    assert sort[0].keys() == ["updated"]


def test_builder_sort_includes_ignore_unmapped():
    """'ignore_unmapped': True is used in the sort clause."""
    builder = query.Builder()

    q = builder.build({})

    assert q["sort"][0]["updated"]["ignore_unmapped"] == True


def test_builder_with_custom_sort():
    """Custom sorts are returned in the query dict."""
    builder = query.Builder()

    q = builder.build({"sort": "title"})

    assert q["sort"] == [{'title': {'ignore_unmapped': True, 'order': 'desc'}}]


def test_builder_order_defaults_to_desc():
    """'order': "desc" is returned in the q dict by default."""
    builder = query.Builder()

    q = builder.build({})

    sort = q["sort"]
    assert sort[0]["updated"]["order"] == "desc"


def test_builder_with_custom_order():
    """'order' params are returned in the query dict if given."""
    builder = query.Builder()

    q = builder.build({"order": "asc"})

    sort = q["sort"]
    assert sort[0]["updated"]["order"] == "asc"


def test_builder_defaults_to_match_all():
    """If no query params are given a "match_all": {} query is returned."""
    builder = query.Builder()

    q = builder.build({})

    assert q["query"] == {"match_all": {}}


def test_builder_default_param_action():
    """Other params are added as "match" clauses."""
    builder = query.Builder()

    q = builder.build({"foo": "bar"})

    assert q["query"] == {"bool": {"must": [{"match": {"foo": "bar"}}]}}


def test_builder_default_params_multidict():
    """Multiple params go into multiple "match" dicts."""
    builder = query.Builder()
    params = multidict.MultiDict()
    params.add("user", "fred")
    params.add("user", "bob")

    q = builder.build(params)

    assert q["query"] == {
        "bool": {
            "must": [
                {"match": {"user": "fred"}},
                {"match": {"user": "bob"}}
            ]
        }
    }


def test_builder_with_evil_arguments():
    builder = query.Builder()
    params = {
        "offset": "3foo",
        "limit": '\' drop table annotations'
    }

    q = builder.build(params)

    assert q["from"] == 0
    assert q["size"] == 20
    assert q["query"] == {'match_all': {}}


def test_builder_passes_params_to_filters():
    testfilter = mock.Mock()
    builder = query.Builder()
    builder.append_filter(testfilter)

    builder.build({"foo": "bar"})

    testfilter.assert_called_with({"foo": "bar"})


def test_builder_ignores_filters_returning_none():
    testfilter = mock.Mock()
    testfilter.return_value = None
    builder = query.Builder()
    builder.append_filter(testfilter)

    q = builder.build({})

    assert q["query"] == {"match_all": {}}


def test_builder_filters_query_by_filter_results():
    testfilter = mock.Mock()
    testfilter.return_value = {"term": {"giraffe": "nose"}}
    builder = query.Builder()
    builder.append_filter(testfilter)

    q = builder.build({})

    assert q["query"] == {
        "filtered": {
            "filter": {"and": [{"term": {"giraffe": "nose"}}]},
            "query": {"match_all": {}},
        },
    }


def test_builder_passes_params_to_matchers():
    testmatcher = mock.Mock()
    builder = query.Builder()
    builder.append_matcher(testmatcher)

    builder.build({"foo": "bar"})

    testmatcher.assert_called_with({"foo": "bar"})


def test_builder_adds_matchers_to_query():
    testmatcher = mock.Mock()
    testmatcher.return_value = {"match": {"giraffe": "nose"}}
    builder = query.Builder()
    builder.append_matcher(testmatcher)

    q = builder.build({})

    assert q["query"] == {
        "bool": {"must": [{"match": {"giraffe": "nose"}}]},
    }


def test_authfilter_world_not_in_principals():
    request = mock.Mock(effective_principals=['foo'])
    authfilter = query.AuthFilter(request)

    assert authfilter({}) == {
        'terms': {'permissions.read': ['group:__world__', 'foo']}
    }


def test_authfilter_world_in_principals():
    request = mock.Mock(effective_principals=['group:__world__', 'foo'])
    authfilter = query.AuthFilter(request)

    assert authfilter({}) == {
        'terms': {'permissions.read': ['group:__world__', 'foo']}
    }


def test_authfilter_with_private_removed_authenticated_userid_principal():
    request = mock.Mock(
        effective_principals=[
            'group:__world__', 'group:foo', 'acct:thom@hypothes.is'],
        authenticated_userid='acct:thom@hypothes.is'
    )
    authfilter = query.AuthFilter(request, private=False)

    assert authfilter({}) == {
        'terms': {'permissions.read': ['group:__world__', 'group:foo']}
    }


def test_groupfilter_term_filters_for_group():
    groupfilter = query.GroupFilter()

    assert groupfilter({"group": "wibble"}) == {"term": {"group": "wibble"}}


def test_groupfilter_strips_param():
    groupfilter = query.GroupFilter()
    params = {"group": "wibble"}

    groupfilter(params)

    assert params == {}


def test_groupfilter_returns_none_when_no_param():
    groupfilter = query.GroupFilter()

    assert groupfilter({}) is None


@pytest.mark.usefixtures('uri')
def test_urifilter_inactive_when_no_uri_param():
    """
    When there's no `uri` parameter, return None.
    """
    request = mock.Mock()
    urifilter = query.UriFilter(request)

    assert urifilter({"foo": "bar"}) is None


def test_urifilter_expands_and_normalizes_into_terms_filter(storage):
    """
    Uses a `terms` filter against target.scope to filter for URI.

    UriFilter should use a `terms` filter against the normalized version of the
    target source field, which we store in `target.scope`.

    It should expand the input URI before searching, and normalize the results
    of the expansion.
    """
    request = mock.Mock()
    storage.expand_uri.side_effect = lambda _, x: [
        "http://giraffes.com/",
        "https://elephants.com/",
    ]

    urifilter = query.UriFilter(request)

    result = urifilter({"uri": "http://example.com/"})
    query_uris = result["terms"]["target.scope"]

    storage.expand_uri.assert_called_with(request.db, "http://example.com/")
    assert sorted(query_uris) == sorted(["http://giraffes.com",
                                         "httpx://giraffes.com",
                                         "https://elephants.com",
                                         "httpx://elephants.com"])


def test_urifilter_queries_multiple_uris(storage):
    """
    Uses a `terms` filter against target.scope to filter for URI.

    When multiple "uri" fields are supplied, the normalized URIs of all of
    them should be collected into a set and sent in the query.
    """
    request = mock.Mock()
    params = multidict.MultiDict()
    params.add("uri", "http://example.com")
    params.add("uri", "http://example.net")
    storage.expand_uri.side_effect = [
        ["http://giraffes.com/", "https://elephants.com/"],
        ["http://tigers.com/", "https://elephants.com/"],
    ]

    urifilter = query.UriFilter(request)

    result = urifilter(params)
    query_uris = result["terms"]["target.scope"]

    storage.expand_uri.assert_any_call(request.db, "http://example.com")
    storage.expand_uri.assert_any_call(request.db, "http://example.net")
    assert sorted(query_uris) == sorted(["http://giraffes.com",
                                         "httpx://giraffes.com",
                                         "https://elephants.com",
                                         "httpx://elephants.com",
                                         "http://tigers.com",
                                         "httpx://tigers.com"])


def test_anymatcher():
    anymatcher = query.AnyMatcher()

    result = anymatcher({"any": "foo"})

    assert result == {
        "simple_query_string": {
            "fields": ["quote", "tags", "text", "uri.parts", "user"],
            "query": "foo",
        }
    }


def test_anymatcher_multiple_params():
    """Multiple keywords at once are handled correctly."""
    anymatcher = query.AnyMatcher()
    params = multidict.MultiDict()
    params.add("any", "howdy")
    params.add("any", "there")

    result = anymatcher(params)

    assert result == {
        "simple_query_string": {
            "fields": ["quote", "tags", "text", "uri.parts", "user"],
            "query": "howdy there",
        }
    }


def test_tagsmatcher_aliases_tag_to_tags():
    """'tag' params should be transformed into 'tags' queries.

    'tag' is aliased to 'tags' because users often type tag instead of tags.

    """
    params = multidict.MultiDict()
    params.add('tag', 'foo')
    params.add('tag', 'bar')

    result = query.TagsMatcher()(params)

    assert list(result.keys()) == ['bool']
    assert list(result['bool'].keys()) == ['must']
    assert len(result['bool']['must']) == 2
    assert {'match': {'tags': {'query': 'foo', 'operator': 'and'}}} in result['bool']['must']
    assert {'match': {'tags': {'query': 'bar', 'operator': 'and'}}} in result['bool']['must']


def test_tagsmatcher_with_both_tag_and_tags():
    """If both 'tag' and 'tags' params are used they should all become tags."""
    params = {'tag': 'foo', 'tags': 'bar'}

    result = query.TagsMatcher()(params)

    assert list(result.keys()) == ['bool']
    assert list(result['bool'].keys()) == ['must']
    assert len(result['bool']['must']) == 2
    assert {'match': {'tags': {'query': 'foo', 'operator': 'and'}}} in result['bool']['must']
    assert {'match': {'tags': {'query': 'bar', 'operator': 'and'}}} in result['bool']['must']


@pytest.fixture
def storage(patch):
    storage = patch('h.api.search.query.storage')
    storage.expand_uri.side_effect = lambda x: [x]
    return storage


@pytest.fixture
def uri(patch):
    uri = patch('h.api.search.query.uri')
    uri.normalize.side_effect = lambda x: x
    return uri
