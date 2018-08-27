# -*- coding: utf-8 -*-

# Most of the tests for `h.search.query` are in `query_test.py` and they
# actually use Elasticsearch. These are the remaining unit tests which mock
# Elasticsearch.

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


# TODO - Move these to `query_test.py`.
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
        testaggregation.return_value = {"terms": {"field": "foo"}}
        builder = query.Builder(ES_VERSION)
        builder.append_aggregation(testaggregation)

        q = builder.build({})

        assert q["aggs"] == {
            "foobar": {"terms": {"field": "foo"}}
        }
