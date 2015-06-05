import mock
from webob import multidict

from h.api import search


def test_build_query_offset_defaults_to_0():
    """If no offset is given then "from": 0 is used in the query by default."""
    query = search.build_query(
        request_params=multidict.NestedMultiDict())

    assert query["from"] == 0


def test_build_query_custom_offsets_are_passed_in():
    """If an offset is given it's returned in the query dict."""
    query = search.build_query(
        request_params=multidict.NestedMultiDict({"offset": 7}))

    assert query["from"] == 7


def test_build_query_offset_string_is_converted_to_int():
    """'offset' arguments should be converted from strings to ints."""
    query = search.build_query(
        request_params=multidict.NestedMultiDict({"offset": "23"}))

    assert query["from"] == 23


def test_build_query_with_invalid_offset():
    """Invalid 'offset' params should be ignored."""
    for invalid_offset in ("foo", '', '   ', "-23", "32.7"):
        query = search.build_query(
            request_params=multidict.NestedMultiDict(
                {"offset": invalid_offset}))

        assert query["from"] == 0


def test_build_query_limit_defaults_to_20():
    """If no limit is given "size": 20 is used in the query by default."""
    query = search.build_query(
        request_params=multidict.NestedMultiDict())

    assert query["size"] == 20


def test_build_query_custom_limits_are_passed_in():
    """If a limit is given it's returned in the query dict as "size"."""
    query = search.build_query(
        request_params=multidict.NestedMultiDict({"limit": 7}))

    assert query["size"] == 7


def test_build_query_limit_strings_are_converted_to_ints():
    """String values for limit should be converted to ints."""
    query = search.build_query(
        request_params=multidict.NestedMultiDict({"limit": "17"}))

    assert query["size"] == 17


def test_build_query_with_invalid_limit():
    """Invalid 'limit' params should be ignored."""
    for invalid_limit in ("foo", '', '   ', "-23", "32.7"):
        query = search.build_query(
            request_params=multidict.NestedMultiDict({"limit": invalid_limit}))

        assert query["size"] == 20  # (20 is the default value.)


def test_build_query_query_defaults_to_match_all():
    """If no query params are given a "match_all": {} query is returned."""
    query = search.build_query(
        request_params=multidict.NestedMultiDict())

    assert query["query"] == {"bool": {"must": [{"match_all": {}}]}}


def test_build_query_sort_is_by_updated():
    """Sort defaults to "updated"."""
    query = search.build_query(
        request_params=multidict.NestedMultiDict())

    sort = query["sort"]
    assert len(sort) == 1
    assert sort[0].keys() == ["updated"]


def test_build_query_sort_includes_ignore_unmapped():
    """'ignore_unmapped': True is used in the sort clause."""
    query = search.build_query(
        request_params=multidict.NestedMultiDict())

    sort = query["sort"]
    assert sort[0]["updated"]["ignore_unmapped"] == True


def test_build_query_with_custom_sort():
    """Custom sorts are returned in the query dict."""
    query = search.build_query(
        request_params=multidict.NestedMultiDict({"sort": "title"}))

    sort = query["sort"]
    assert sort == [{'title': {'ignore_unmapped': True, 'order': 'desc'}}]


def test_build_query_order_defaults_to_desc():
    """'order': "desc" is returned in the query dict by default."""
    query = search.build_query(
        request_params=multidict.NestedMultiDict())

    sort = query["sort"]
    assert sort[0]["updated"]["order"] == "desc"


def test_build_query_with_custom_order():
    """'order' params are returned in the query dict if given."""
    query = search.build_query(
        request_params=multidict.NestedMultiDict({"order": "asc"}))

    sort = query["sort"]
    assert sort[0]["updated"]["order"] == "asc"


def test_build_query_for_user():
    """'user' params returned in the query dict in "match" clauses."""
    query = search.build_query(
        request_params=multidict.NestedMultiDict({"user": "bob"}))

    assert query["query"] == {
        "bool": {"must": [{"match": {"user": "bob"}}]}}


def test_build_query_for_multiple_users():
    """Multiple "user" params go into multiple "match" dicts."""
    params = multidict.MultiDict()
    params.add("user", "fred")
    params.add("user", "bob")

    query = search.build_query(request_params=params)

    assert query["query"] == {
        "bool": {
            "must": [
                {"match": {"user": "fred"}},
                {"match": {"user": "bob"}}
            ]
        }
    }


def test_build_query_for_tag():
    """'tags' params are returned in the query dict in "match" clauses."""
    query = search.build_query(
        request_params=multidict.NestedMultiDict({"tags": "foo"}))

    assert query["query"] == {
        "bool": {"must": [{"match": {"tags": "foo"}}]}}


def test_build_query_for_multiple_tags():
    """Multiple "tags" params go into multiple "match" dicts."""
    params = multidict.MultiDict()
    params.add("tags", "foo")
    params.add("tags", "bar")

    query = search.build_query(request_params=params)

    assert query["query"] == {
        "bool": {
            "must": [
                {"match": {"tags": "foo"}},
                {"match": {"tags": "bar"}}
            ]
        }
    }


def test_build_query_with_combined_user_and_tag_query():
    """A 'user' and a 'param' at the same time are handled correctly."""
    query = search.build_query(
        request_params=multidict.NestedMultiDict(
            {"user": "bob", "tags": "foo"}))

    assert query["query"] == {
        "bool": {"must": [
            {"match": {"user": "bob"}},
            {"match": {"tags": "foo"}},
        ]}}


def test_build_query_with_keyword():
    """Keywords are returned in the query dict in a "multi_match" clause."""
    params = multidict.MultiDict()
    params.add("any", "howdy")

    query = search.build_query(request_params=params)

    assert query["query"] == {
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


def test_build_query_with_multiple_keywords():
    """Multiple keywords at once are handled correctly."""
    params = multidict.MultiDict()
    params.add("any", "howdy")
    params.add("any", "there")

    query = search.build_query(request_params=params)

    assert query["query"] == {
        "bool": {"must": [{"multi_match": {
            "fields": ["quote", "tags", "text", "uri.parts", "user"],
            "query": ["howdy", "there"],
            "type": "cross_fields"
        }}]}
    }


def test_build_query_for_uri():
    """'uri' args are returned in the query dict in a "match" clause.

    This is what happens when you open the sidebar on a page and it loads
    all the annotations of that page.

    """
    query = search.build_query(
        request_params=multidict.NestedMultiDict(
            {"uri": "http://example.com/"}))

    assert query["query"] == {
        "bool": {"must": [{"match": {"uri": "http://example.com/"}}]}}


def test_build_query_with_single_text_param():
    """'text' params are returned in the query dict in "match" clauses."""
    query = search.build_query(
        request_params=multidict.NestedMultiDict({"text": "foobar"}))

    assert query["query"] == {
        "bool": {"must": [{"match": {"text": "foobar"}}]}}


def test_build_query_with_multiple_text_params():
    """Multiple "test" request params produce multiple "match" clauses."""
    params = multidict.MultiDict()
    params.add("text", "foo")
    params.add("text", "bar")
    query = search.build_query(request_params=params)

    assert query["query"] == {
        "bool": {
            "must": [
                {"match": {"text": "foo"}},
                {"match": {"text": "bar"}}
            ]
        }
    }


def test_build_query_with_single_quote_param():
    """'quote' params are returned in the query dict in "match" clauses."""
    query = search.build_query(
        request_params=multidict.NestedMultiDict({"quote": "foobar"}))

    assert query["query"] == {
        "bool": {"must": [{"match": {"quote": "foobar"}}]}}


def test_build_query_with_multiple_quote_params():
    """Multiple "quote" request params produce multiple "match" clauses."""
    params = multidict.MultiDict()
    params.add("quote", "foo")
    params.add("quote", "bar")
    query = search.build_query(request_params=params)

    assert query["query"] == {
        "bool": {
            "must": [
                {"match": {"quote": "foo"}},
                {"match": {"quote": "bar"}}
            ]
        }
    }


def test_build_query_with_evil_arguments():
    params = multidict.NestedMultiDict({
        "offset": "3foo",
        "limit": '\' drop table annotations'
    })

    query = search.build_query(request_params=params)

    assert query["query"] == {'bool': {'must': [{'match_all': {}}]}}


@mock.patch("annotator.annotation.Annotation.search_raw")
def test_search_with_user_object(search_raw):
    """If search() gets a user arg it passes it to search_raw().

    Note: This test is testing the function's user param. You can also
    pass one or more user arguments in the request.params, those are
    tested elsewhere.

    """
    user = mock.MagicMock()

    search.search(request_params=multidict.NestedMultiDict(), user=user)

    first_call = search_raw.call_args_list[0]
    assert first_call[1]["user"] == user


@mock.patch("h.api.search.search")
def test_index_limit_is_20(search_func):
    """index() calls search with "limit": 20."""
    search.index()

    first_call = search_func.call_args_list[0]
    assert first_call[0][0]["limit"] == 20
