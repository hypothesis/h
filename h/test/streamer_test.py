# -*- coding: utf-8 -*-
"""Defines unit tests for h.streamer."""

import unittest

from collections import namedtuple
import json

from mock import ANY
from mock import MagicMock, Mock
from mock import patch
from pyramid.testing import DummyRequest

from h.streamer import FilterToElasticFilter
from h.streamer import WebSocket
from h.streamer import should_send_event
from h.streamer import broadcast_from_queue
from h.streamer import websocket


FakeMessage = namedtuple('FakeMessage', 'body')


class FakeSocket(object):
    client_id = None
    filter = None
    request = None
    terminated = None

    def __init__(self, client_id):
        self.client_id = client_id
        self.terminated = False
        self.filter = MagicMock()
        self.request = MagicMock()
        self.send = MagicMock()


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
    }

    fef = FilterToElasticFilter(filter_json, request)
    assert fef.query['query'] == {"match_all": {}}


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
    }

    generated = FilterToElasticFilter(filter_json, request)
    query = generated.query['query']['bool']['must'][0]
    expected = 'foo bar'

    assert query['term']['text'] == expected


def test_websocket_bad_origin(config):
    config.registry.settings.update({'origins': 'http://good'})
    config.include('h.streamer')
    req = DummyRequest(headers={'Origin': 'http://bad'})
    res = websocket(req)
    assert res.code == 403


def test_websocket_good_origin(config):
    config.registry.settings.update({'origins': 'http://good'})
    config.include('h.streamer')
    req = DummyRequest(headers={'Origin': 'http://good'})
    req.get_response = MagicMock()
    res = websocket(req)
    assert res.code != 403


def test_websocket_same_origin(config):
    config.include('h.streamer')
    # example.com is the dummy request default host URL
    req = DummyRequest(headers={'Origin': 'http://example.com'})
    req.get_response = MagicMock()
    res = websocket(req)
    assert res.code != 403


class TestWebSocket(unittest.TestCase):
    def setUp(self):
        fake_request = MagicMock()
        fake_socket = MagicMock()

        self.s = WebSocket(fake_socket)
        self.s.request = fake_request

    def test_opened_starts_reader(self):
        self.s.opened()
        self.s.request.get_queue_reader.assert_called_once_with('annotations', ANY)

    def test_filter_message_with_uri_gets_patched(self):
        filter_message = json.dumps({
            'filter': {
                'actions': {},
                'match_policy': 'include_all',
                'clauses': [{
                    'field': '/uri',
                    'operator': 'equals',
                    'value': 'http://example.com',
                }],
            }
        })

        with patch('annotator.document.Document.get_by_uri') as doc:
            uris = Mock()
            uris.return_value = ['http://example.com',
                                 'http://example.com/alter',
                                 'http://example.com/print']
            doc.return_value = Mock(uris=uris)
            msg = MagicMock()
            msg.data = filter_message

            self.s.received_message(msg)

            uri_filter = self.s.filter.filter['clauses'][0]
            uri_values = uri_filter['value']
            assert len(uri_values) == 3
            assert 'http://example.com' in uri_values
            assert 'http://example.com/alter' in uri_values
            assert 'http://example.com/print' in uri_values


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

        self.queue = MagicMock()
        self.queue.__iter__.return_value = self.messages

        self.should_patcher = patch('h.streamer.should_send_event')
        self.should = self.should_patcher.start()

    def tearDown(self):
        self.should_patcher.stop()

    def test_send_when_socket_should_receive_event(self):
        self.should.return_value = True
        sock = FakeSocket('giraffe')
        broadcast_from_queue(self.queue, [sock])
        assert sock.send.called

    def test_no_send_when_socket_should_not_receive_event(self):
        self.should.return_value = False
        sock = FakeSocket('pidgeon')
        broadcast_from_queue(self.queue, [sock])
        assert sock.send.called is False


class TestShouldSendEvent(unittest.TestCase):
    def setUp(self):
        self.sock_giraffe = FakeSocket('giraffe')
        self.sock_giraffe.filter.match.return_value = True

        self.sock_pigeon = FakeSocket('pigeon')

        self.sock_roadkill = FakeSocket('roadkill')
        self.sock_roadkill.terminated = True

    def test_non_sending_socket_receives_event(self):
        data = {'action': 'update', 'src_client_id': 'pigeon'}
        assert should_send_event(self.sock_giraffe, {}, data)

    def test_sending_socket_does_not_receive_event(self):
        data = {'action': 'update', 'src_client_id': 'pigeon'}
        assert should_send_event(self.sock_pigeon, {}, data) is False

    def test_terminated_socket_does_not_recieve_event(self):
        data = {'action': 'update', 'src_client_id': 'pigeon'}
        assert should_send_event(self.sock_roadkill, {}, data) is False

    def test_should_send_event_no_filter(self):
        self.sock_giraffe.filter = None
        data = {'action': 'update', 'src_client_id': 'pigeon'}
        assert should_send_event(self.sock_giraffe, {}, data) is False

    def test_should_send_event_doesnt_send_reads(self):
        data = {'action': 'read', 'src_client_id': 'pigeon'}
        assert should_send_event(self.sock_giraffe, {}, data) is False

    def test_should_send_event_filtered(self):
        self.sock_pigeon.filter.match.return_value = False
        data = {'action': 'update', 'src_client_id': 'giraffe'}
        assert should_send_event(self.sock_pigeon, {}, data) is False

    def test_should_send_event_check_permissions(self):
        self.sock_giraffe.request.has_permission.return_value = False
        anno = object()
        data = {'action': 'update', 'src_client_id': 'pigeon'}
        sock = self.sock_giraffe
        assert should_send_event(sock, anno, data) is False
        assert sock.request.has_permission.called_with('read', anno)
