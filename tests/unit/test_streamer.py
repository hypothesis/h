# -*- coding: utf-8 -*-
"""Defines unit tests for h.streamer."""

from mock import patch
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
    """Test the query size limit
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
    """Test the query size limit
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
    """Test the include_any match policy
    """
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
    """Test the include_all match policy
    """
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
    """Test the exclude_any match policy
    """
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
    """Test the exclude_all match policy
    """
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
    """Test if the correct operator fn is called
    """
    """Test the query size limit
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

    with patch.object(FilterToElasticFilter, 'equals') as eq:
        eq.return_value = ""
        FilterToElasticFilter(filter_json, request)
    assert eq.called
