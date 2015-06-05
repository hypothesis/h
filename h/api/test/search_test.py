"""Tests for h/api/search.py."""
import mock
import webob.multidict

import h.api.search as search


@mock.patch("annotator.annotation.Annotation.search_raw")
def test_search_offset_defaults_to_0(search_raw):
    """If no offset is given search_raw() is called with "from": 0."""
    search.search(request_params=webob.multidict.NestedMultiDict())

    first_call = search_raw.call_args_list[0]
    assert first_call[0][0]["from"] == 0


@mock.patch("annotator.annotation.Annotation.search_raw")
def test_search_custom_offsets_are_passed_in(search_raw):
    """If an offset is given it's passed to search_raw() as "from"."""
    search.search(
        request_params=webob.multidict.NestedMultiDict({"offset": 7}))

    first_call = search_raw.call_args_list[0]
    assert first_call[0][0]["from"] == 7


@mock.patch("annotator.annotation.Annotation.search_raw")
def test_search_offset_string_is_converted_to_int(search_raw):
    """'offset' arguments should be converted from strings to ints."""
    search.search(request_params={"offset": "23"})

    first_call = search_raw.call_args_list[0]
    assert first_call[0][0]["from"] == 23


@mock.patch("annotator.annotation.Annotation.search_raw")
def test_search_with_invalid_offset(search_raw):
    """Invalid 'offset' params should be ignored."""
    for invalid_offset in ("foo", '', '   ', "-23", "32.7"):
        search.search(request_params={"offset": invalid_offset})

        first_call = search_raw.call_args_list[0]
        assert first_call[0][0]["from"] == 0


@mock.patch("annotator.annotation.Annotation.search_raw")
def test_search_limit_defaults_to_20(search_raw):
    """If no limit is given search_raw() is called with "size": 20."""
    search.search(request_params=webob.multidict.NestedMultiDict())

    first_call = search_raw.call_args_list[0]
    assert first_call[0][0]["size"] == 20


@mock.patch("annotator.annotation.Annotation.search_raw")
def test_search_custom_limits_are_passed_in(search_raw):
    """If a limit is given it's passed to search_raw() as "size"."""
    search.search(request_params=webob.multidict.NestedMultiDict({"limit": 7}))

    first_call = search_raw.call_args_list[0]
    assert first_call[0][0]["size"] == 7


@mock.patch("annotator.annotation.Annotation.search_raw")
def test_search_limit_strings_are_converted_to_ints(search_raw):
    """String values for limit should be converted to ints."""
    search.search(request_params={"limit": "17"})

    first_call = search_raw.call_args_list[0]
    assert first_call[0][0]["size"] == 17


@mock.patch("annotator.annotation.Annotation.search_raw")
def test_search_with_invalid_limit(search_raw):
    """Invalid 'limit' params should be ignored."""
    for invalid_limit in ("foo", '', '   ', "-23", "32.7"):
        search.search(request_params={"limit": invalid_limit})

        first_call = search_raw.call_args_list[0]
        assert first_call[0][0]["size"] == 20  # (20 is the default value.)


@mock.patch("annotator.annotation.Annotation.search_raw")
def test_search_query_defaults_to_match_all(search_raw):
    """If no query is given search_raw is called with "match_all": {}."""
    search.search(request_params=webob.multidict.NestedMultiDict())

    first_call = search_raw.call_args_list[0]
    query = first_call[0][0]["query"]
    assert query == {"bool": {"must": [{"match_all": {}}]}}


@mock.patch("annotator.annotation.Annotation.search_raw")
def test_search_sort_is_by_updated(search_raw):
    """search_raw() is called with sort "updated"."""
    search.search(request_params=webob.multidict.NestedMultiDict())

    first_call = search_raw.call_args_list[0]
    sort = first_call[0][0]["sort"]
    assert len(sort) == 1
    assert sort[0].keys() == ["updated"]


@mock.patch("annotator.annotation.Annotation.search_raw")
def test_search_sort_includes_ignore_unmapped(search_raw):
    """'ignore_unmapped': True is automatically passed to search_raw()."""
    search.search(request_params=webob.multidict.NestedMultiDict())

    first_call = search_raw.call_args_list[0]
    sort = first_call[0][0]["sort"]
    assert sort[0]["updated"]["ignore_unmapped"] == True


@mock.patch("annotator.annotation.Annotation.search_raw")
def test_search_with_custom_sort(search_raw):
    """Custom sorts should be passed on to search_raw()."""
    search.search(
        request_params=webob.multidict.NestedMultiDict({"sort": "title"}))

    first_call = search_raw.call_args_list[0]

    sort = first_call[0][0]["sort"]
    assert sort == [{'title': {'ignore_unmapped': True, 'order': 'desc'}}]


@mock.patch("annotator.annotation.Annotation.search_raw")
def test_search_order_defaults_to_desc(search_raw):
    """'order': "desc" is to search_raw()."""
    search.search(request_params=webob.multidict.NestedMultiDict())

    first_call = search_raw.call_args_list[0]
    sort = first_call[0][0]["sort"]
    assert sort[0]["updated"]["order"] == "desc"


@mock.patch("annotator.annotation.Annotation.search_raw")
def test_search_with_custom_order(search_raw):
    """'order' params are passed to search_raw() if given."""
    search.search(
        request_params=webob.multidict.NestedMultiDict({"order": "asc"}))

    first_call = search_raw.call_args_list[0]

    sort = first_call[0][0]["sort"]
    assert sort[0]["updated"]["order"] == "asc"


@mock.patch("annotator.annotation.Annotation.search_raw")
def test_search_for_user(search_raw):
    """'user' params are passed to search_raw() in the "match"."""
    search.search(
        request_params=webob.multidict.NestedMultiDict({"user": "bob"}))

    first_call = search_raw.call_args_list[0]
    query = first_call[0][0]["query"]
    assert query == {
        "bool": {"must": [{"match": {"user": "bob"}}]}}


@mock.patch("annotator.annotation.Annotation.search_raw")
def test_search_for_multiple_users(search_raw):
    """Multiple "user" params go into multiple "match" dicts."""
    params = webob.multidict.MultiDict()
    params.add("user", "fred")
    params.add("user", "bob")

    search.search(request_params=params)

    first_call = search_raw.call_args_list[0]
    query = first_call[0][0]["query"]
    assert query == {
        "bool": {
            "must": [
                {"match": {"user": "fred"}},
                {"match": {"user": "bob"}}
            ]
        }
    }


@mock.patch("annotator.annotation.Annotation.search_raw")
def test_search_for_tag(search_raw):
    """'tags' params are passed to search_raw() in the "match"."""
    search.search(
        request_params=webob.multidict.NestedMultiDict({"tags": "foo"}))

    first_call = search_raw.call_args_list[0]
    query = first_call[0][0]["query"]
    assert query == {
        "bool": {"must": [{"match": {"tags": "foo"}}]}}


@mock.patch("annotator.annotation.Annotation.search_raw")
def test_search_for_multiple_tags(search_raw):
    """Multiple "tags" params go into multiple "match" dicts."""
    params = webob.multidict.MultiDict()
    params.add("tags", "foo")
    params.add("tags", "bar")

    search.search(request_params=params)

    first_call = search_raw.call_args_list[0]
    query = first_call[0][0]["query"]
    assert query == {
        "bool": {
            "must": [
                {"match": {"tags": "foo"}},
                {"match": {"tags": "bar"}}
            ]
        }
    }


@mock.patch("annotator.annotation.Annotation.search_raw")
def test_search_with_combined_user_and_tag_query(search_raw):
    """A 'user' and a 'param' at the same time are handled correctly."""
    search.search(
        request_params=webob.multidict.NestedMultiDict(
            {"user": "bob", "tags": "foo"}))

    first_call = search_raw.call_args_list[0]
    query = first_call[0][0]["query"]
    assert query == {
        "bool": {"must": [
            {"match": {"user": "bob"}},
            {"match": {"tags": "foo"}},
        ]}}


@mock.patch("annotator.annotation.Annotation.search_raw")
def test_search_with_keyword(search_raw):
    """Keywords are passed to search_raw() as a multi_match query."""
    params = webob.multidict.MultiDict()
    params.add("any", "howdy")

    search.search(request_params=params)

    first_call = search_raw.call_args_list[0]
    query = first_call[0][0]["query"]
    assert query == {
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


@mock.patch("annotator.annotation.Annotation.search_raw")
def test_search_with_multiple_keywords(search_raw):
    """Multiple keywords at once are handled correctly."""
    params = webob.multidict.MultiDict()
    params.add("any", "howdy")
    params.add("any", "there")

    search.search(request_params=params)

    first_call = search_raw.call_args_list[0]
    query = first_call[0][0]["query"]
    assert query == {
        "bool": {"must": [{"multi_match": {
            "fields": ["quote", "tags", "text", "uri.parts", "user"],
            "query": ["howdy", "there"],
            "type": "cross_fields"
        }}]}
    }


@mock.patch("annotator.annotation.Annotation.search_raw")
def test_search_for_uri(search_raw):
    """_search() passes "uri" args on to search_raw() in the "match" dict.

    This is what happens when you open the sidebar on a page and it loads
    all the annotations of that page.

    """
    search.search(
        request_params=webob.multidict.NestedMultiDict(
            {"uri": "http://example.com/"}))

    first_call = search_raw.call_args_list[0]
    query = first_call[0][0]["query"]
    assert query == {
        "bool": {"must": [{"match": {"uri": "http://example.com/"}}]}}


@mock.patch("annotator.annotation.Annotation.search_raw")
def test_search_with_single_text_param(search_raw):
    """_search() passes "text" params to search_raw() in a "match" dict."""
    search.search(
        request_params=webob.multidict.NestedMultiDict({"text": "foobar"}))

    first_call = search_raw.call_args_list[0]
    query = first_call[0][0]["query"]
    assert query == {
        "bool": {"must": [{"match": {"text": "foobar"}}]}}


@mock.patch("annotator.annotation.Annotation.search_raw")
def test_search_with_multiple_text_params(search_raw):
    """Multiple "test" request params produce multiple "match" dicts."""
    params = webob.multidict.MultiDict()
    params.add("text", "foo")
    params.add("text", "bar")
    search.search(request_params=params)

    first_call = search_raw.call_args_list[0]
    query = first_call[0][0]["query"]
    assert query == {
        "bool": {
            "must": [
                {"match": {"text": "foo"}},
                {"match": {"text": "bar"}}
            ]
        }
    }


@mock.patch("annotator.annotation.Annotation.search_raw")
def test_search_with_single_quote_param(search_raw):
    """_search() passes a "quote" param to search_raw() in a "match"."""
    search.search(
        request_params=webob.multidict.NestedMultiDict({"quote": "foobar"}))

    first_call = search_raw.call_args_list[0]
    query = first_call[0][0]["query"]
    assert query == {
        "bool": {"must": [{"match": {"quote": "foobar"}}]}}


@mock.patch("annotator.annotation.Annotation.search_raw")
def test_search_with_multiple_quote_params(search_raw):
    """Multiple "quote" request params produce multiple "match" dicts."""
    params = webob.multidict.MultiDict()
    params.add("quote", "foo")
    params.add("quote", "bar")
    search.search(request_params=params)

    first_call = search_raw.call_args_list[0]
    query = first_call[0][0]["query"]
    assert query == {
        "bool": {
            "must": [
                {"match": {"quote": "foo"}},
                {"match": {"quote": "bar"}}
            ]
        }
    }


@mock.patch("annotator.annotation.Annotation.search_raw")
def test_search_with_user_object(search_raw):
    """If _search() gets a user arg it passes it to search_raw().

    Note: This test is testing the function's user param. You can also
    pass one or more user arguments in the request.params, those are
    tested elsewhere.

    """
    user = mock.MagicMock()

    search.search(request_params=webob.multidict.NestedMultiDict(), user=user)

    first_call = search_raw.call_args_list[0]
    assert first_call[1]["user"] == user


@mock.patch("annotator.annotation.Annotation.search_raw")
def test_search_with_evil_arguments(search_raw):
    params = webob.multidict.NestedMultiDict({
        "offset": "3foo",
        "limit": '\' drop table annotations'
    })

    search.search(request_params=params)

    first_call = search_raw.call_args_list[0]
    query = first_call[0][0]["query"]
    assert query == {'bool': {'must': [{'match_all': {}}]}}
