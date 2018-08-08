# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import mock
import pytest
from hypothesis import strategies as st
from hypothesis import given
from webob import multidict

from h.search import query

ES_VERSION = (1, 7, 0)
MISSING = object()

OFFSET_DEFAULT = 0
LIMIT_DEFAULT = 20
LIMIT_MAX = 200


class TestBuilder(object):
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
    def test_offset(self, offset, from_):
        builder = query.Builder(ES_VERSION)

        if offset is MISSING:
            q = builder.build({})
        else:
            q = builder.build({"offset": offset})

        assert q["from"] == from_

    @given(st.text())
    @pytest.mark.fuzz
    def test_limit_output_within_bounds(self, text):
        """Given any string input, output should be in the allowed range."""
        builder = query.Builder(ES_VERSION)

        q = builder.build({"limit": text})

        assert isinstance(q["size"], int)
        assert 0 <= q["size"] <= LIMIT_MAX

    @given(st.integers())
    @pytest.mark.fuzz
    def test_limit_output_within_bounds_int_input(self, lim):
        """Given any integer input, output should be in the allowed range."""
        builder = query.Builder(ES_VERSION)

        q = builder.build({"limit": str(lim)})

        assert isinstance(q["size"], int)
        assert 0 <= q["size"] <= LIMIT_MAX

    @given(st.integers(min_value=0, max_value=LIMIT_MAX))
    @pytest.mark.fuzz
    def test_limit_matches_input(self, lim):
        """Given an integer in the allowed range, it should be passed through."""
        builder = query.Builder(ES_VERSION)

        q = builder.build({"limit": str(lim)})

        assert q["size"] == lim

    def test_limit_missing(self):
        builder = query.Builder(ES_VERSION)

        q = builder.build({})

        assert q["size"] == LIMIT_DEFAULT

    def test_sort_is_by_updated(self):
        """Sort defaults to "updated"."""
        builder = query.Builder(ES_VERSION)

        q = builder.build({})

        sort = q["sort"]
        assert len(sort) == 1
        assert list(sort[0].keys()) == ["updated"]

    def test_with_custom_sort(self):
        """Custom sorts are returned in the query dict."""
        builder = query.Builder(ES_VERSION)

        q = builder.build({"sort": "title"})

        assert q["sort"] == [{'title': {'unmapped_type': 'boolean', 'order': 'desc'}}]

    def test_order_defaults_to_desc(self):
        """'order': "desc" is returned in the q dict by default."""
        builder = query.Builder(ES_VERSION)

        q = builder.build({})

        sort = q["sort"]
        assert sort[0]["updated"]["order"] == "desc"

    def test_with_custom_order(self):
        """'order' params are returned in the query dict if given."""
        builder = query.Builder(ES_VERSION)

        q = builder.build({"order": "asc"})

        sort = q["sort"]
        assert sort[0]["updated"]["order"] == "asc"

    def test_defaults_to_match_all(self):
        """If no query params are given a "match_all": {} query is returned."""
        builder = query.Builder(ES_VERSION)

        q = builder.build({})

        assert q["query"] == {'bool': {'filter': [], 'must': []}}

    def test_default_param_action(self):
        """Other params are added as "match" clauses."""
        builder = query.Builder(ES_VERSION)

        q = builder.build({"foo": "bar"})

        assert q["query"] == {
            'bool': {'filter': [],
                     'must': [{'match': {'foo': 'bar'}}]},
        }

    def test_default_params_multidict(self):
        """Multiple params go into multiple "match" dicts."""
        builder = query.Builder(ES_VERSION)
        params = multidict.MultiDict()
        params.add("user", "fred")
        params.add("user", "bob")

        q = builder.build(params)

        assert q["query"] == {
            'bool': {'filter': [],
                     'must': [{'match': {'user': 'fred'}},
                              {'match': {'user': 'bob'}}]},
        }

    def test_with_evil_arguments(self):
        builder = query.Builder(ES_VERSION)
        params = {
            "offset": "3foo",
            "limit": '\' drop table annotations'
        }

        q = builder.build(params)

        assert q["from"] == 0
        assert q["size"] == 20
        assert q["query"] == {'bool': {'filter': [], 'must': []}}

    def test_passes_params_to_filters(self):
        testfilter = mock.Mock()
        builder = query.Builder(ES_VERSION)
        builder.append_filter(testfilter)

        builder.build({"foo": "bar"})

        testfilter.assert_called_with({"foo": "bar"})

    def test_ignores_filters_returning_none(self):
        testfilter = mock.Mock()
        testfilter.return_value = None
        builder = query.Builder(ES_VERSION)
        builder.append_filter(testfilter)

        q = builder.build({})

        assert q["query"] == {'bool': {'filter': [], 'must': []}}

    def test_filters_query_by_filter_results(self):
        testfilter = mock.Mock()
        testfilter.return_value = {"term": {"giraffe": "nose"}}
        builder = query.Builder(ES_VERSION)
        builder.append_filter(testfilter)

        q = builder.build({})
        assert q["query"] == {
            'bool': {'filter': [{'term': {'giraffe': 'nose'}}],
                     'must': []},
        }

    def test_passes_params_to_matchers(self):
        testmatcher = mock.Mock()
        builder = query.Builder(ES_VERSION)
        builder.append_matcher(testmatcher)

        builder.build({"foo": "bar"})

        testmatcher.assert_called_with({"foo": "bar"})

    def test_adds_matchers_to_query(self):
        testmatcher = mock.Mock()
        testmatcher.return_value = {"match": {"giraffe": "nose"}}
        builder = query.Builder(ES_VERSION)
        builder.append_matcher(testmatcher)

        q = builder.build({})

        assert q["query"] == {
            'bool': {'filter': [],
                     'must': [{'match': {'giraffe': 'nose'}}]},
        }

    def test_passes_params_to_aggregations(self):
        testaggregation = mock.Mock()
        builder = query.Builder(ES_VERSION)
        builder.append_aggregation(testaggregation)

        builder.build({"foo": "bar"})

        testaggregation.assert_called_with({"foo": "bar"})

    def test_adds_aggregations_to_query(self):
        testaggregation = mock.Mock(key="foobar")
        # testaggregation.key.return_value = "foobar"
        testaggregation.return_value = {"terms": {"field": "foo"}}
        builder = query.Builder(ES_VERSION)
        builder.append_aggregation(testaggregation)

        q = builder.build({})

        assert q["aggs"] == {
            "foobar": {"terms": {"field": "foo"}}
        }


def test_authority_filter_adds_authority_term():
    filter_ = query.AuthorityFilter(authority='partner.org')
    assert filter_({}) == {'term': {'authority': 'partner.org'}}


class TestAuthFilter(object):
    def test_unauthenticated(self):
        request = mock.Mock(authenticated_userid=None)
        authfilter = query.AuthFilter(request)

        assert authfilter({}) == {'term': {'shared': True}}

    def test_authenticated(self):
        request = mock.Mock(authenticated_userid='acct:doe@example.org')
        authfilter = query.AuthFilter(request)

        assert authfilter({}) == {
            'bool': {
                'should': [
                    {'term': {'shared': True}},
                    {'term': {'user_raw': 'acct:doe@example.org'}},
                ],
            }
        }


class TestGroupFilter(object):
    def test_term_filters_for_group(self):
        groupfilter = query.GroupFilter()

        assert groupfilter({"group": "wibble"}) == {"term": {"group": "wibble"}}

    def test_strips_param(self):
        groupfilter = query.GroupFilter()
        params = {"group": "wibble"}

        groupfilter(params)

        assert params == {}

    def test_returns_none_when_no_param(self):
        groupfilter = query.GroupFilter()

        assert groupfilter({}) is None


class TestGroupAuthFilter(object):
    def test_fetches_readable_groups(self, pyramid_request, group_service):
        pyramid_request.user = mock.sentinel.user

        filter_ = query.GroupAuthFilter(pyramid_request)
        filter_({})

        group_service.groupids_readable_by.assert_called_once_with(mock.sentinel.user)

    def test_returns_terms_filter(self, pyramid_request, group_service):
        group_service.groupids_readable_by.return_value = ['group-a', 'group-b']

        filter_ = query.GroupAuthFilter(pyramid_request)
        result = filter_({})

        assert result == {'terms': {'group': ['group-a', 'group-b']}}


class TestUriFilter(object):
    @pytest.mark.usefixtures('uri')
    def test_inactive_when_no_uri_param(self):
        """
        When there's no `uri` parameter, return None.
        """
        request = mock.Mock()
        urifilter = query.UriFilter(request)

        assert urifilter({"foo": "bar"}) is None

    def test_expands_and_normalizes_into_terms_filter(self, storage):
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
        assert sorted(query_uris) == sorted(["httpx://giraffes.com",
                                             "httpx://elephants.com"])

    def test_queries_multiple_uris(self, storage):
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
        assert sorted(query_uris) == sorted(["httpx://giraffes.com",
                                             "httpx://elephants.com",
                                             "httpx://tigers.com"])

    def test_accepts_url_aliases(self, storage):
        request = mock.Mock()
        params = multidict.MultiDict()
        params.add("uri", "http://example.com")
        params.add("url", "http://example.net")
        storage.expand_uri.side_effect = [
            ["http://giraffes.com/", "https://elephants.com/"],
            ["http://tigers.com/", "https://elephants.com/"],
        ]

        urifilter = query.UriFilter(request)

        result = urifilter(params)
        query_uris = result["terms"]["target.scope"]

        storage.expand_uri.assert_any_call(request.db, "http://example.com")
        storage.expand_uri.assert_any_call(request.db, "http://example.net")
        assert sorted(query_uris) == sorted(["httpx://giraffes.com",
                                             "httpx://elephants.com",
                                             "httpx://tigers.com"])

    @pytest.fixture
    def storage(self, patch):
        storage = patch('h.search.query.storage')
        storage.expand_uri.side_effect = lambda x: [x]
        return storage

    @pytest.fixture
    def uri(self, patch):
        uri = patch('h.search.query.uri')
        uri.normalize.side_effect = lambda x: x
        return uri


class TestUserFilter(object):
    def test_term_filters_for_user(self):
        userfilter = query.UserFilter()

        assert userfilter({"user": "luke"}) == {"terms": {"user": ["luke"]}}

    def test_supports_filtering_for_multiple_users(self):
        userfilter = query.UserFilter()

        params = multidict.MultiDict()
        params.add("user", "alice")
        params.add("user", "luke")

        assert userfilter(params) == {
            "terms": {
                "user": ["alice", "luke"]
            }
        }

    def test_lowercases_value(self):
        userfilter = query.UserFilter()

        assert userfilter({"user": "LUkE"}) == {"terms": {"user": ["luke"]}}

    def test_strips_param(self):
        userfilter = query.UserFilter()
        params = {"user": "luke"}

        userfilter(params)

        assert params == {}

    def test_returns_none_when_no_param(self):
        userfilter = query.UserFilter()

        assert userfilter({}) is None


class TestDeletedFilter(object):
    def test_filter(self):
        deletedfilter = query.DeletedFilter()

        assert deletedfilter({}) == {
            "bool": {"must_not": {"exists": {"field": "deleted"}}}
        }


class TestAnyMatcher():
    def test_any_query(self):
        anymatcher = query.AnyMatcher()

        result = anymatcher({"any": "foo"})

        assert result == {
            "simple_query_string": {
                "fields": ["quote", "tags", "text", "uri.parts"],
                "query": "foo",
            }
        }

    def test_multiple_params(self):
        """Multiple keywords at once are handled correctly."""
        anymatcher = query.AnyMatcher()
        params = multidict.MultiDict()
        params.add("any", "howdy")
        params.add("any", "there")

        result = anymatcher(params)

        assert result == {
            "simple_query_string": {
                "fields": ["quote", "tags", "text", "uri.parts"],
                "query": "howdy there",
            }
        }

    def test_aliases_tag_to_tags(self):
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

    def test_with_both_tag_and_tags(self):
        """If both 'tag' and 'tags' params are used they should all become tags."""
        params = {'tag': 'foo', 'tags': 'bar'}

        result = query.TagsMatcher()(params)

        assert list(result.keys()) == ['bool']
        assert list(result['bool'].keys()) == ['must']
        assert len(result['bool']['must']) == 2
        assert {'match': {'tags': {'query': 'foo', 'operator': 'and'}}} in result['bool']['must']
        assert {'match': {'tags': {'query': 'bar', 'operator': 'and'}}} in result['bool']['must']


class TestTagsAggregations(object):
    def test_key_is_tags(self):
        assert query.TagsAggregation().key == 'tags'

    def test_elasticsearch_aggregation(self):
        agg = query.TagsAggregation()
        assert agg({}) == {
            'terms': {'field': 'tags_raw', 'size': 10}
        }

    def test_it_allows_to_set_a_limit(self):
        agg = query.TagsAggregation(limit=14)
        assert agg({}) == {
            'terms': {'field': 'tags_raw', 'size': 14}
        }

    def test_parse_result(self):
        agg = query.TagsAggregation()
        elasticsearch_result = {
            'buckets': [
                {'key': 'tag-4', 'doc_count': 42},
                {'key': 'tag-2', 'doc_count': 28},
            ]
        }

        assert agg.parse_result(elasticsearch_result) == [
            {'tag': 'tag-4', 'count': 42},
            {'tag': 'tag-2', 'count': 28},
        ]


class TestUsersAggregation(object):
    def test_key_is_users(self):
        assert query.UsersAggregation().key == 'users'

    def test_elasticsearch_aggregation(self):
        agg = query.UsersAggregation()
        assert agg({}) == {
            'terms': {'field': 'user_raw', 'size': 10}
        }

    def test_it_allows_to_set_a_limit(self):
        agg = query.UsersAggregation(limit=14)
        assert agg({}) == {
            'terms': {'field': 'user_raw', 'size': 14}
        }

    def test_parse_result(self):
        agg = query.UsersAggregation()
        elasticsearch_result = {
            'buckets': [
                {'key': 'alice', 'doc_count': 42},
                {'key': 'luke', 'doc_count': 28},
            ]
        }

        assert agg.parse_result(elasticsearch_result) == [
            {'user': 'alice', 'count': 42},
            {'user': 'luke', 'count': 28},
        ]


class TestNipsaFilter(object):
    def test_call_returns_nipsa_filter(self, pyramid_request, nipsa_filter):
        f = query.NipsaFilter(pyramid_request)

        assert f({}) == nipsa_filter.return_value

    def test_call_passes_group_service(self, pyramid_request, nipsa_filter, group_service):
        f = query.NipsaFilter(pyramid_request)

        f({})

        nipsa_filter.assert_called_once_with(group_service, mock.ANY)

    def test_call_passes_request_user(self, pyramid_request, nipsa_filter):
        f = query.NipsaFilter(pyramid_request)

        f({})

        nipsa_filter.assert_called_once_with(mock.ANY, pyramid_request.user)

    @pytest.fixture
    def nipsa_filter(self, patch):
        return patch('h.search.query.nipsa_filter')


def test_nipsa_filter_filters_out_nipsad_annotations(group_service):
    """nipsa_filter() filters out annotations with "nipsa": True."""
    assert query.nipsa_filter(group_service) == {
        "bool": {
            "should": [
                {'bool': {'must_not': {'term': {'nipsa': True}}}},
                {'exists': {'field': 'thread_ids'}},
            ]
        }
    }


def test_nipsa_filter_users_own_annotations_are_not_filtered(group_service, user):
    filter_ = query.nipsa_filter(group_service, user)

    assert {'term': {'user': 'fred'}} in (
        filter_["bool"]["should"])


def test_nipsa_filter_coerces_userid_to_lowercase(group_service, user):
    user.userid = 'DonkeyNose'

    filter_ = query.nipsa_filter(group_service, user)

    assert {'term': {'user': 'donkeynose'}} in (
        filter_["bool"]["should"])


def test_nipsa_filter_group_annotations_not_filtered_for_creator(group_service, user):
    group_service.groupids_created_by.return_value = ['pubid-1', 'pubid-4', 'pubid-3']

    filter_ = query.nipsa_filter(group_service, user)

    assert {'terms': {'group': ['pubid-1', 'pubid-4', 'pubid-3']}} in (
        filter_['bool']['should'])


@pytest.fixture
def user():
    return mock.Mock(userid='fred')
