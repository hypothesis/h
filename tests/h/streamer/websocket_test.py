# -*- coding: utf-8 -*-

from collections import namedtuple
import json
from pyramid import testing

from gevent.queue import Queue
import mock

from h.streamer import websocket


FakeMessage = namedtuple('FakeMessage', ['data'])


def test_websocket_stores_instance_list():
    socket = mock.Mock()
    clients = [websocket.WebSocket(socket), websocket.WebSocket(socket)]

    for c in clients:
        assert c in websocket.WebSocket.instances


def test_websocket_removes_self_from_instance_list_when_closed():
    socket = mock.Mock()
    client1 = websocket.WebSocket(socket)
    client2 = websocket.WebSocket(socket)

    assert len(websocket.WebSocket.instances) == 2
    client1.closed(1000)
    assert client1 not in websocket.WebSocket.instances
    client2.closed(1000)
    assert client2 not in websocket.WebSocket.instances

    # A second closure (however unusual) should not raise
    client1.closed(1000)


def test_socket_enqueues_incoming_messages():
    queue = Queue()
    request = testing.DummyRequest()
    request.registry['streamer.work_queue'] = queue
    socket = mock.Mock()
    client = websocket.WebSocket(socket)
    client.request = request
    message = FakeMessage('client data')

    client.received_message(message)
    result = queue.get_nowait()

    assert result.socket == client
    assert result.payload == 'client data'


def test_handle_message_clears_feature_cache():
    socket = mock.Mock()
    message = websocket.Message(socket=socket, payload=json.dumps({
        'messageType': 'foo'}))
    websocket.handle_message(message)

    socket.request.feature.clear.assert_called_with()


def test_handle_message_sets_socket_client_id_for_client_id_messages():
    socket = mock.Mock()
    socket.client_id = None
    message = websocket.Message(socket=socket, payload=json.dumps({
        'messageType': 'client_id',
        'value': 'abcd1234',
    }))

    websocket.handle_message(message)

    assert socket.client_id == 'abcd1234'


@mock.patch('h.api.storage.expand_uri')
def test_handle_message_sets_socket_filter_for_filter_messages(expand_uri):
    expand_uri.return_value = ['http://example.com']
    socket = mock.Mock()
    socket.filter = None
    message = websocket.Message(socket=socket, payload=json.dumps({
        'filter': {
            'actions': {},
            'match_policy': 'include_all',
            'clauses': [{
                'field': '/uri',
                'operator': 'equals',
                'value': 'http://example.com',
            }],
        }
    }))

    websocket.handle_message(message)

    assert socket.filter is not None


@mock.patch('h.api.storage.expand_uri')
def test_handle_message_expands_uris_in_uri_filter(expand_uri):
    expand_uri.return_value = ['http://example.com',
                               'http://example.com/alter',
                               'http://example.com/print']
    socket = mock.Mock()
    socket.filter = None
    message = websocket.Message(socket=socket, payload=json.dumps({
        'filter': {
            'actions': {},
            'match_policy': 'include_all',
            'clauses': [{
                'field': '/uri',
                'operator': 'equals',
                'value': 'http://example.com',
            }],
        }
    }))

    websocket.handle_message(message)

    uri_filter = socket.filter.filter['clauses'][0]
    uri_values = uri_filter['value']
    assert len(uri_values) == 3
    assert 'http://example.com' in uri_values
    assert 'http://example.com/alter' in uri_values
    assert 'http://example.com/print' in uri_values
