# -*- coding: utf-8 -*-
"""Defines unit tests for h.streamer."""

import unittest

from mock import MagicMock
from mock import patch
from pyramid.testing import DummyRequest

from h.streamer import FilterToElasticFilter
from h.streamer import StreamClient
from h.streamer import annotation_packet


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


def test_annotation_packet():
    res = annotation_packet(['foo', 'bar'], 'read')
    assert res['payload'] == ['foo', 'bar']
    assert res['type'] == 'annotation-notification'
    assert res['options']['action'] == 'read'


class TestStreamClient(unittest.TestCase):
    def setUp(self):
        self.session = MagicMock()
        self.session.filter.match.return_value = True
        self.c = StreamClient(self.session)

    def test_send_annotation_event_no_filter(self):
        self.session.filter = None

        self.c.send_annotation_event({}, 'update')
        assert self.session.send.called

    def test_send_annotation_event_doesnt_send_reads(self):
        self.c.send_annotation_event({}, 'read')
        assert not self.session.send.called

    def test_send_annotation_event_filtered(self):
        self.session.filter.match.return_value = False

        self.c.send_annotation_event({}, 'update')
        assert not self.session.send.called

    def test_send_annotation_event_check_permissions(self):
        self.session.request.has_permission.return_value = False

        anno = object()

        self.c.send_annotation_event(anno, 'update')
        assert not self.session.send.called
        assert self.session.request.has_permission.called_with('read', anno)
