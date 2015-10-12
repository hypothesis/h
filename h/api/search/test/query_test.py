# -*- coding: utf-8 -*-

import pytest
import mock
from webob import multidict

from h.api.search import query


def test_builder_offset_defaults_to_0():
    """If no offset is given then "from": 0 is used in the query by default."""
    builder = query.Builder()

    q = builder.build({})

    assert q["from"] == 0


def test_builder_custom_offsets_are_passed_in():
    """If an offset is given it's returned in the query dict."""
    builder = query.Builder()

    q = builder.build({"offset": 7})

    assert q["from"] == 7


def test_builder_offset_string_is_converted_to_int():
    """'offset' arguments should be converted from strings to ints."""
    builder = query.Builder()

    q = builder.build({"offset": "23"})

    assert q["from"] == 23


def test_builder_with_invalid_offset():
    """Invalid 'offset' params should be ignored."""
    for invalid_offset in ("foo", '', '   ', "-23", "32.7"):
        builder = query.Builder()

        q = builder.build({"offset": invalid_offset})

        assert q["from"] == 0


def test_builder_limit_defaults_to_20():
    """If no limit is given "size": 20 is used in the query by default."""
    builder = query.Builder()

    q = builder.build({})

    assert q["size"] == 20


def test_builder_custom_limits_are_passed_in():
    """If a limit is given it's returned in the query dict as "size"."""
    builder = query.Builder()

    q = builder.build({"limit": 7})

    assert q["size"] == 7


def test_builder_limit_strings_are_converted_to_ints():
    """String values for limit should be converted to ints."""
    builder = query.Builder()

    q = builder.build({"limit": "17"})

    assert q["size"] == 17


def test_builder_with_invalid_limit():
    """Invalid 'limit' params should be ignored."""
    for invalid_limit in ("foo", '', '   ', "-23", "32.7"):
        builder = query.Builder()

        q = builder.build({"limit": invalid_limit})

        assert q["size"] == 20  # (20 is the default value.)


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

    assert q["query"] == {"bool": {"should": [{"match": {"foo": "bar"}}]}}


def test_builder_default_params_multidict():
    """Multiple params go into multiple "match" dicts."""
    builder = query.Builder()
    params = multidict.MultiDict()
    params.add("user", "fred")
    params.add("user", "bob")

    q = builder.build(params)

    assert q["query"] == {
        "bool": {
            "should": [
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
        "bool": {"should": [{"match": {"giraffe": "nose"}}]},
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


def test_groupfilter_restricts_to_public_annotations_when_feature_off():
    """
    When the groups feature flag is off, the filter should ensure that only
    public annotations are returned, regardless of the parameter value.
    """
    request = mock.Mock()
    request.feature.return_value = False
    groupfilter = query.GroupFilter(request)

    assert groupfilter({}) == groupfilter({"group": "foo"}) == {
        "term": {"group": "__world__"}}


def test_groupfilter_strips_param_when_feature_off():
    """
    When the groups feature flag is off, the filter should strip the group
    parameter.
    """
    request = mock.Mock()
    request.feature.return_value = False
    groupfilter = query.GroupFilter(request)
    params = {"group": "wibble"}

    groupfilter(params)

    assert params == {}


def test_groupfilter_term_filters_for_group():
    request = mock.Mock()
    groupfilter = query.GroupFilter(request)

    assert groupfilter({"group": "wibble"}) == {"term": {"group": "wibble"}}


def test_groupfilter_strips_param():
    request = mock.Mock()
    groupfilter = query.GroupFilter(request)
    params = {"group": "wibble"}

    groupfilter(params)

    assert params == {}


def test_groupfilter_returns_none_when_no_param():
    request = mock.Mock()
    groupfilter = query.GroupFilter(request)

    assert groupfilter({}) is None


@pytest.mark.usefixtures('uri')
def test_urifilter_inactive_when_no_uri_param():
    """
    When there's no `uri` parameter, return None.
    """
    urifilter = query.UriFilter()

    assert urifilter({"foo": "bar"}) is None


def test_urifilter_expands_and_normalizes_into_terms_filter(uri):
    """
    Uses a `terms` filter against target.scope to filter for URI.

    UriFilter should use a `terms` filter against the normalized version of the
    target source field, which we store in `target.scope`.

    It should expand the input URI before searching, and normalize the results
    of the expansion.
    """
    uri.expand.side_effect = lambda x: [
        "http://giraffes.com/",
        "https://elephants.com/",
    ]
    uri.normalize.side_effect = lambda x: x[:-1]  # Strip the trailing slash
    urifilter = query.UriFilter()

    result = urifilter({"uri": "http://example.com/"})

    uri.expand.assert_called_with("http://example.com/")

    assert result == {"terms":
        {"target.scope": ["http://giraffes.com", "https://elephants.com"]}
    }


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

    assert result == {'terms': {'tags': ['foo', 'bar']}}


def test_tagsmatcher_with_both_tag_and_tags():
    """If both 'tag' and 'tags' params are used they should all become tags."""
    params = {'tag': 'foo', 'tags': 'bar'}

    result = query.TagsMatcher()(params)

    assert result == {'terms': {'tags': ['foo', 'bar']}}


@pytest.fixture
def uri(request):
    patcher = mock.patch('h.api.search.query.uri', autospec=True)
    uri = patcher.start()
    uri.expand.side_effect = lambda x: [x]
    uri.normalize.side_effect = lambda x: x
    request.addfinalizer(patcher.stop)
    return uri
