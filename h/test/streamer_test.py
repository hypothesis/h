# -*- coding: utf-8 -*-
"""Defines unit tests for h.streamer."""

from mock import patch, MagicMock
from pyramid.testing import DummyRequest
from h.streamer import FilterToElasticFilter


# Tests for the FilterToElasticFilter class
# this class needs a python request, and a filter json object as the input
def test_zero_clauses():
    """No condition is given so a match_all query should be generated
    """
    request = DummyRequest()
    filter_json = {
        'clauses': [],
        'past_data': {'load_past': 'none'}
    }

    fef = FilterToElasticFilter(filter_json, request)
    assert fef.query['query'] == {"match_all": {}}


def test_hits():
    """Test setting the query size limit right
    """
    request = DummyRequest()
    filter_json = {
        'match_policy': 'include_all',
        'clauses': [{
            'field': 'text',
            'operator': 'equals',
            'value': 'foo bar',
            'options': {}
        }],
        'past_data': {
            'load_past': 'hits',
            'hits': 75
        }
    }

    fef = FilterToElasticFilter(filter_json, request)
    assert fef.query['size'] is 75


def test_past_time():
    """Test setting the time range filter right
    """
    request = DummyRequest()
    filter_json = {
        'match_policy': 'include_all',
        'clauses': [{
            'field': 'text',
            'operator': 'equals',
            'value': 'foo bar',
            'options': {}
        }],
        'past_data': {
            'load_past': 'time',
            'go_back': 60
        }
    }

    fef = FilterToElasticFilter(filter_json, request)
    assert 'gte' in fef.query['filter']['range']['created']


def test_policy_include_any():
    request = DummyRequest()
    filter_json = {
        'match_policy': 'include_any',
        'clauses': [{
            'field': 'text',
            'operator': 'equals',
            'value': 'foo',
            'options': {}
        }, {
            'field': 'tag',
            'operator': 'equals',
            'value': 'bar',
            'options': {}
        }],
        'past_data': {'load_past': 'none'}
    }

    fef = FilterToElasticFilter(filter_json, request)
    assert 'should' in fef.query['query']['bool']


def test_policy_include_all():
    request = DummyRequest()
    filter_json = {
        'match_policy': 'include_all',
        'clauses': [{
            'field': 'text',
            'operator': 'equals',
            'value': 'foo',
            'options': {}
        }, {
            'field': 'tag',
            'operator': 'equals',
            'value': 'bar',
            'options': {}
        }],
        'past_data': {'load_past': 'none'}
    }

    fef = FilterToElasticFilter(filter_json, request)
    assert 'must' in fef.query['query']['bool']


def test_policy_exclude_any():
    request = DummyRequest()
    filter_json = {
        'match_policy': 'exclude_any',
        'clauses': [{
            'field': 'text',
            'operator': 'equals',
            'value': 'foo',
            'options': {}
        }, {
            'field': 'tag',
            'operator': 'equals',
            'value': 'bar',
            'options': {}
        }],
        'past_data': {'load_past': 'none'}
    }

    fef = FilterToElasticFilter(filter_json, request)
    assert 'must_not' in fef.query['query']['bool']


def test_policy_exclude_all():
    request = DummyRequest()
    filter_json = {
        'match_policy': 'exclude_all',
        'clauses': [{
            'field': 'text',
            'operator': 'equals',
            'value': 'foo',
            'options': {}
        }, {
            'field': 'tag',
            'operator': 'equals',
            'value': 'bar',
            'options': {}
        }],
        'past_data': {'load_past': 'none'}
    }

    fef = FilterToElasticFilter(filter_json, request)
    assert 'must' in fef.query['query']['bool']['must_not']['bool']


def test_operator_call():
    request = DummyRequest()

    filter_json = {
        'match_policy': 'include_all',
        'clauses': [{
            'field': '/text',
            'operator': 'equals',
            'value': 'foo bar',
            'options': {
                'es': {
                    'query_type': 'simple'
                }
            }
        }],
        'past_data': {
            'load_past': 'time',
            'go_back': 60
        }
    }

    generated = FilterToElasticFilter(filter_json, request)
    query = generated.query['query']['bool']['must'][0]
    expected = 'foo bar'

    assert query['term']['text'] == expected
