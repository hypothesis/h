# -*- coding: utf-8 -*-
"""Defines unit tests for h.streamer."""

import unittest

from collections import namedtuple
import json

from mock import MagicMock
from mock import call
from mock import patch
from pyramid.testing import DummyRequest

from h.streamer import FilterToElasticFilter
from h.streamer import send_annotation_event
from h.streamer import broadcast_from_queue


FakeMessage = namedtuple('FakeMessage', 'body')
FakeSession = namedtuple('FakeSession', 'client_id')


def has_ordered_sublist(lst, sublist):
    """
    Determines whether the passed list contains, in the specified order, all
    the elements in sublist.
    """
    sub_idx = 0
    max_idx = len(sublist) - 1
    for x in lst:
        if x == sublist[sub_idx]:
            sub_idx += 1
        if sub_idx > max_idx:
            return True
    return sub_idx > max_idx


class ObjectIncluding(object):
    def __init__(self, include):
        self.include = include

    def __eq__(self, other):
        try:
            for k, v in self.include.items():
                if other[k] != v:
                    return False
        except (KeyError, TypeError):
            return False
        else:
            return True


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


class TestBroadcast(unittest.TestCase):
    def setUp(self):
        self.message_data = [
            {'annotation': {'id': 1},
             'action': 'delete',
             'src_client_id': 'pigeon'},
            {'annotation': {'id': 2},
             'action': 'update',
             'src_client_id': 'pigeon'},
            {'annotation': {'id': 3},
             'action': 'delete',
             'src_client_id': 'cat'},
        ]
        self.messages = [FakeMessage(json.dumps(m)) for m in self.message_data]
        self.sess_giraffe = FakeSession('giraffe')
        self.sess_pigeon = FakeSession('pigeon')

        self.queue = MagicMock()
        self.queue.__iter__.return_value = self.messages

        self.manager = MagicMock()
        self.manager.active_sessions.return_value = [self.sess_giraffe,
                                                     self.sess_pigeon]

        self.send_patcher = patch('h.streamer.send_annotation_event')
        self.send = self.send_patcher.start()

    def tearDown(self):
        self.send_patcher.stop()

    def test_non_sending_session_receives_all(self):
        broadcast_from_queue(self.queue, self.manager)

        sess = self.sess_giraffe

        expected = [
            call(sess, ObjectIncluding({'id': 1}), 'delete'),
            call(sess, ObjectIncluding({'id': 2}), 'update'),
            call(sess, ObjectIncluding({'id': 3}), 'delete'),
        ]

        assert has_ordered_sublist(self.send.mock_calls, expected)

    def test_sending_session_does_not_receive_own(self):
        broadcast_from_queue(self.queue, self.manager)

        sess = self.sess_pigeon

        expected = call(sess, ObjectIncluding({'id': 3}), 'delete')
        unexpected = [
            call(sess, ObjectIncluding({'id': 1}), 'delete'),
            call(sess, ObjectIncluding({'id': 2}), 'update'),
        ]

        assert expected in self.send.mock_calls
        for c in unexpected:
            assert c not in self.send.mock_calls


class TestSendAnnotationEvent(unittest.TestCase):
    def setUp(self):
        self.session = MagicMock()
        self.session.filter.match.return_value = True

    def test_send_annotation_event_no_filter(self):
        self.session.filter = None

        send_annotation_event(self.session, {}, 'update')
        assert self.session.send.called

    def test_send_annotation_event_doesnt_send_reads(self):
        send_annotation_event(self.session, {}, 'read')
        assert not self.session.send.called

    def test_send_annotation_event_filtered(self):
        self.session.filter.match.return_value = False

        send_annotation_event(self.session, {}, 'update')
        assert not self.session.send.called

    def test_send_annotation_event_check_permissions(self):
        self.session.request.has_permission.return_value = False

        anno = object()

        send_annotation_event(self.session, anno, 'update')
        assert not self.session.send.called
        assert self.session.request.has_permission.called_with('read', anno)
