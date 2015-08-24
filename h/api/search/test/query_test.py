# -*- coding: utf-8 -*-

import pytest
import mock
from webob import multidict
from pyramid import testing

from h.api.search import query


# The fixtures required to mock all of build()'s dependencies.
build_fixtures = pytest.mark.usefixtures('nipsa', 'groups', 'uri')


@build_fixtures
def test_build_offset_defaults_to_0():
    """If no offset is given then "from": 0 is used in the query by default."""
    q = query.build(multidict.NestedMultiDict(), [])

    assert q["from"] == 0


@build_fixtures
def test_build_custom_offsets_are_passed_in():
    """If an offset is given it's returned in the query dict."""
    q = query.build(multidict.NestedMultiDict({"offset": 7}), [])

    assert q["from"] == 7


@build_fixtures
def test_build_offset_string_is_converted_to_int():
    """'offset' arguments should be converted from strings to ints."""
    q = query.build(multidict.NestedMultiDict({"offset": "23"}), [])

    assert q["from"] == 23


@build_fixtures
def test_build_with_invalid_offset():
    """Invalid 'offset' params should be ignored."""
    for invalid_offset in ("foo", '', '   ', "-23", "32.7"):
        q = query.build(multidict.NestedMultiDict({"offset": invalid_offset}),
                        [])

        assert q["from"] == 0


@build_fixtures
def test_build_limit_defaults_to_20():
    """If no limit is given "size": 20 is used in the query by default."""
    q = query.build(multidict.NestedMultiDict(), [])

    assert q["size"] == 20


@build_fixtures
def test_build_custom_limits_are_passed_in():
    """If a limit is given it's returned in the query dict as "size"."""
    q = query.build(multidict.NestedMultiDict({"limit": 7}), [])

    assert q["size"] == 7


@build_fixtures
def test_build_limit_strings_are_converted_to_ints():
    """String values for limit should be converted to ints."""
    q = query.build(multidict.NestedMultiDict({"limit": "17"}), [])

    assert q["size"] == 17


@build_fixtures
def test_build_with_invalid_limit():
    """Invalid 'limit' params should be ignored."""
    for invalid_limit in ("foo", '', '   ', "-23", "32.7"):
        q = query.build(
            multidict.NestedMultiDict({"limit": invalid_limit}), [])

        assert q["size"] == 20  # (20 is the default value.)


@build_fixtures
def test_build_defaults_to_match_all():
    """If no query params are given a "match_all": {} query is returned."""
    q = query.build(multidict.NestedMultiDict(), [])

    assert q["query"]["filtered"]["query"] == {"match_all": {}}


@build_fixtures
def test_build_sort_is_by_updated():
    """Sort defaults to "updated"."""
    q = query.build(multidict.NestedMultiDict(), [])

    sort = q["sort"]
    assert len(sort) == 1
    assert sort[0].keys() == ["updated"]


@build_fixtures
def test_build_sort_includes_ignore_unmapped():
    """'ignore_unmapped': True is used in the sort clause."""
    q = query.build(multidict.NestedMultiDict(), [])

    sort = q["sort"]
    assert sort[0]["updated"]["ignore_unmapped"] == True


@build_fixtures
def test_build_with_custom_sort():
    """Custom sorts are returned in the query dict."""
    q = query.build(multidict.NestedMultiDict({"sort": "title"}), [])

    sort = q["sort"]
    assert sort == [{'title': {'ignore_unmapped': True, 'order': 'desc'}}]


@build_fixtures
def test_build_order_defaults_to_desc():
    """'order': "desc" is returned in the q dict by default."""
    q = query.build(multidict.NestedMultiDict(), [])

    sort = q["sort"]
    assert sort[0]["updated"]["order"] == "desc"


@build_fixtures
def test_build_with_custom_order():
    """'order' params are returned in the query dict if given."""
    q = query.build(multidict.NestedMultiDict({"order": "asc"}), [])

    sort = q["sort"]
    assert sort[0]["updated"]["order"] == "asc"


@build_fixtures
def test_build_for_user():
    """'user' params returned in the query dict in "match" clauses."""
    q = query.build(multidict.NestedMultiDict({"user": "bob"}), [])

    assert q["query"]["filtered"]["query"] == {
        "bool": {"must": [{"match": {"user": "bob"}}]}}


@build_fixtures
def test_build_for_multiple_users():
    """Multiple "user" params go into multiple "match" dicts."""
    params = multidict.MultiDict()
    params.add("user", "fred")
    params.add("user", "bob")

    q = query.build(params, [])

    assert q["query"]["filtered"]["query"] == {
        "bool": {
            "must": [
                {"match": {"user": "fred"}},
                {"match": {"user": "bob"}}
            ]
        }
    }


@build_fixtures
def test_build_for_tag():
    """'tags' params are returned in the query dict in "match" clauses."""
    q = query.build(multidict.NestedMultiDict({"tags": "foo"}), [])

    assert q["query"]["filtered"]["query"] == {
        "bool": {"must": [{"match": {"tags": "foo"}}]}}


@build_fixtures
def test_build_for_multiple_tags():
    """Multiple "tags" params go into multiple "match" dicts."""
    params = multidict.MultiDict()
    params.add("tags", "foo")
    params.add("tags", "bar")

    q = query.build(params, [])

    assert q["query"]["filtered"]["query"] == {
        "bool": {
            "must": [
                {"match": {"tags": "foo"}},
                {"match": {"tags": "bar"}}
            ]
        }
    }


@build_fixtures
def test_build_with_combined_user_and_tag_query():
    """A 'user' and a 'param' at the same time are handled correctly."""
    q = query.build(
        multidict.NestedMultiDict({"user": "bob", "tags": "foo"}), [])

    assert q["query"]["filtered"]["query"] == {
        "bool": {"must": [
            {"match": {"user": "bob"}},
            {"match": {"tags": "foo"}},
        ]}}


@build_fixtures
def test_build_with_keyword():
    """Keywords are returned in the query dict in a "multi_match" clause."""
    params = multidict.MultiDict()
    params.add("any", "howdy")

    q = query.build(params, [])

    assert q["query"]["filtered"]["query"] == {
        "bool": {
            "must": [
                {
                    "multi_match": {
                        "fields": ["quote", "tags", "text", "uri.parts",
                                   "user"],
                        "query": ["howdy"],
                        "type": "cross_fields"
                    }
                }
            ]
        }
    }


@build_fixtures
def test_build_with_multiple_keywords():
    """Multiple keywords at once are handled correctly."""
    params = multidict.MultiDict()
    params.add("any", "howdy")
    params.add("any", "there")

    q = query.build(params, [])

    assert q["query"]["filtered"]["query"] == {
        "bool": {"must": [{"multi_match": {
            "fields": ["quote", "tags", "text", "uri.parts", "user"],
            "query": ["howdy", "there"],
            "type": "cross_fields"
        }}]}
    }


@build_fixtures
def test_build_for_uri(uri):
    """'uri' args are returned in the query dict in a "match" clause.

    This is what happens when you open the sidebar on a page and it loads
    all the annotations of that page.

    """
    uri.expand.side_effect = lambda x: [x]
    uri.normalize.side_effect = lambda x: x

    q1 = query.build(
        multidict.NestedMultiDict({"uri": "http://example.com/"}), [])
    q2 = query.build(
        multidict.NestedMultiDict({"uri": "http://whitehouse.gov/"}), [])

    assert q1["query"]["filtered"]["query"] == {
        "bool": {"must": [{"match": {"uri": "http://example.com/"}}]}}
    assert q2["query"]["filtered"]["query"] == {
        "bool": {"must": [{"match": {"uri": "http://whitehouse.gov/"}}]}}


@build_fixtures
def test_build_for_uri_with_multiple_representations(uri):
    """It should expand the search to all URIs.

    If h.api.uri.expand returns multiple documents for the URI then
    build() should return a query that finds annotations that match one
    or more of these documents' URIs.

    """
    results = ["http://example.com/",
               "http://example2.com/",
               "http://example3.com/"]
    uri.expand.side_effect = lambda x: results
    uri.normalize.side_effect = lambda x: x

    q = query.build(
        multidict.NestedMultiDict({"uri": "http://example.com/"}), [])

    assert q["query"]["filtered"]["query"] == {
        "bool": {
            "must": [
                {
                    "bool": {
                        "minimum_should_match": 1,
                        "should": [
                            {"match": {"uri": "http://example.com/"}},
                            {"match": {"uri": "http://example2.com/"}},
                            {"match": {"uri": "http://example3.com/"}}
                        ]
                    }
                }
            ]
        }
    }


@mock.patch("h.api.search.query.uri")
def test_build_for_uri_normalized(uri):
    """
    Uses a term filter against target.source_normalized to filter for URI.

    When querying for a URI with search_normalized_uris set to true, build
    should use a term filter against the normalized version of the target
    source field.

    It should expand the input URI before searching, and normalize the results
    of the expansion.
    """
    uri.expand.side_effect = lambda x: [
        "http://giraffes.com/",
        "https://elephants.com/",
    ]
    uri.normalize.side_effect = lambda x: x[:-1]  # Strip the trailing slash

    params = multidict.NestedMultiDict({"uri": "http://example.com/"})

    q = query.build(params, [], search_normalized_uris=True)

    uri.expand.assert_called_with("http://example.com/")

    expected_filter = {"or": [
        {"term": {"target.source_normalized": "http://giraffes.com"}},
        {"term": {"target.source_normalized": "https://elephants.com"}},
    ]}
    assert expected_filter in q["query"]["filtered"]["filter"]["and"]


@build_fixtures
def test_build_with_single_text_param():
    """'text' params are returned in the query dict in "match" clauses."""
    q = query.build(multidict.NestedMultiDict({"text": "foobar"}), [])

    assert q["query"]["filtered"]["query"] == {
        "bool": {"must": [{"match": {"text": "foobar"}}]}}


@build_fixtures
def test_build_with_multiple_text_params():
    """Multiple "test" request params produce multiple "match" clauses."""
    params = multidict.MultiDict()
    params.add("text", "foo")
    params.add("text", "bar")
    q = query.build(params, [])

    assert q["query"]["filtered"]["query"] == {
        "bool": {
            "must": [
                {"match": {"text": "foo"}},
                {"match": {"text": "bar"}}
            ]
        }
    }


@build_fixtures
def test_build_with_single_quote_param():
    """'quote' params are returned in the query dict in "match" clauses."""
    q = query.build(multidict.NestedMultiDict({"quote": "foobar"}), [])

    assert q["query"]["filtered"]["query"] == {
        "bool": {"must": [{"match": {"quote": "foobar"}}]}}


@build_fixtures
def test_build_with_multiple_quote_params():
    """Multiple "quote" request params produce multiple "match" clauses."""
    params = multidict.MultiDict()
    params.add("quote", "foo")
    params.add("quote", "bar")
    q = query.build(params, [])

    assert q["query"]["filtered"]["query"] == {
        "bool": {
            "must": [
                {"match": {"quote": "foo"}},
                {"match": {"quote": "bar"}}
            ]
        }
    }


@build_fixtures
def test_build_with_evil_arguments():
    params = multidict.NestedMultiDict({
        "offset": "3foo",
        "limit": '\' drop table annotations'
    })

    q = query.build(params, [])

    assert q["query"]["filtered"]["query"] == {'match_all': {}}


@build_fixtures
def test_build_returns_nipsa_filter(nipsa):
    """_build() returns a nipsa-filtered query."""
    nipsa.nipsa_filter.return_value = "foobar!"

    q = query.build(multidict.NestedMultiDict(), [])

    assert "foobar!" in q["query"]["filtered"]["filter"]["and"]


@build_fixtures
def test_build_does_not_pass_userid_to_nipsa_filter(nipsa):
    query.build(multidict.NestedMultiDict(), [])
    assert nipsa.nipsa_filter.call_args[1]["userid"] is None


@build_fixtures
def test_build_does_pass_userid_to_nipsa_filter(nipsa):
    query.build(multidict.NestedMultiDict(), [], userid='fred')
    assert nipsa.nipsa_filter.call_args[1]["userid"] == "fred"


@build_fixtures
def test_build_with_arbitrary_params():
    """You can pass any ?foo=bar param to the search API.

    Arbitrary parameters that aren't handled specially are simply passed to
    Elasticsearch as match clauses. This way search queries can match against
    any fields in the Elasticsearch object.

    """
    params = multidict.NestedMultiDict({"foo.bar": "arbitrary"})

    q = query.build(params, [])

    assert q["query"]["filtered"]["query"] == {
        'bool': {
            'must': [
                {
                    'match': {'foo.bar': 'arbitrary'}
                }
            ]
        }
    }


@build_fixtures
def test_build_nipsa_filter_is_included(nipsa):
    request = mock.Mock(authenticated_userid='fred', effective_principals=[])
    q = query.build(multidict.NestedMultiDict(), [])

    assert nipsa.nipsa_filter.return_value in (
        q["query"]["filtered"]["filter"]["and"])


@build_fixtures
def test_build_passes_request_to_group_filter(groups):
    effective_principals = mock.Mock()

    query.build(multidict.NestedMultiDict(), effective_principals)

    groups.group_filter.assert_called_once_with(effective_principals)


@build_fixtures
def test_build_groups_filter_is_included(groups):
    query_ = query.build(multidict.NestedMultiDict(), [])

    assert groups.group_filter.return_value in (
        query_["query"]["filtered"]["filter"]["and"])


@pytest.fixture
def nipsa(request):
    patcher = mock.patch('h.api.search.query.nipsa', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def groups(request):
    patcher = mock.patch('h.api.search.query.groups', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def uri(request):
    patcher = mock.patch('h.api.search.query.uri', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()
