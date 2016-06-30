# -*- coding: utf-8 -*-

from collections import namedtuple
import json

import mock
import pytest
from gevent.queue import Queue
from pyramid import security

from h.streamer import websocket


FakeMessage = namedtuple('FakeMessage', ['data'])


def test_websocket_stores_instance_list(fake_environ):
    socket = mock.Mock()
    clients = [
        websocket.WebSocket(socket, environ=fake_environ),
        websocket.WebSocket(socket, environ=fake_environ)
    ]

    for c in clients:
        assert c in websocket.WebSocket.instances


def test_websocket_removes_self_from_instance_list_when_closed(fake_environ):
    socket = mock.Mock()
    client1 = websocket.WebSocket(socket, environ=fake_environ)
    client2 = websocket.WebSocket(socket, environ=fake_environ)

    assert len(websocket.WebSocket.instances) == 2
    client1.closed(1000)
    assert client1 not in websocket.WebSocket.instances
    client2.closed(1000)
    assert client2 not in websocket.WebSocket.instances

    # A second closure (however unusual) should not raise
    client1.closed(1000)


def test_socket_enqueues_incoming_messages(fake_environ):
    socket = mock.Mock()
    client = websocket.WebSocket(socket, environ=fake_environ)
    message = FakeMessage('client data')
    queue = fake_environ['h.ws.streamer_work_queue']

    client.received_message(message)
    result = queue.get_nowait()

    assert result.socket == client
    assert result.payload == 'client data'


def test_socket_sets_auth_data_from_environ(fake_environ):
    socket = mock.Mock()
    client = websocket.WebSocket(socket, environ=fake_environ)

    assert client.authenticated_userid == 'janet'
    assert client.effective_principals == [
        security.Everyone,
        security.Authenticated,
        'group:__world__',
    ]


def test_socket_sets_registry_from_environ(fake_environ):
    socket = mock.Mock()
    client = websocket.WebSocket(socket, environ=fake_environ)

    assert client.registry == mock.sentinel.registry


def test_handle_message_sets_socket_client_id_for_client_id_messages():
    socket = mock.Mock()
    socket.client_id = None
    message = websocket.Message(socket=socket, payload=json.dumps({
        'messageType': 'client_id',
        'value': 'abcd1234',
    }))

    websocket.handle_message(message)

    assert socket.client_id == 'abcd1234'


def test_handle_message_sets_socket_filter_for_filter_messages():
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
def test_handle_message_expands_uris_in_uri_filter_with_session(expand_uri):
    expand_uri.return_value = ['http://example.com',
                               'http://example.com/alter',
                               'http://example.com/print']
    session = mock.sentinel.db_session
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

    websocket.handle_message(message, session=session)

    uri_filter = socket.filter.filter['clauses'][0]
    uri_values = uri_filter['value']
    assert len(uri_values) == 3
    assert 'http://example.com' in uri_values
    assert 'http://example.com/alter' in uri_values
    assert 'http://example.com/print' in uri_values


@mock.patch('h.api.storage.expand_uri')
def test_handle_message_expands_uris_using_passed_session(expand_uri):
    expand_uri.return_value = ['http://example.com', 'http://example.org/']
    session = mock.sentinel.db_session
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

    websocket.handle_message(message, session=session)

    expand_uri.assert_called_once_with(session, 'http://example.com')


@pytest.fixture
def fake_environ():
    return {
        'h.ws.authenticated_userid': 'janet',
        'h.ws.effective_principals': [security.Everyone,
                                      security.Authenticated,
                                      'group:__world__',],
        'h.ws.registry': mock.sentinel.registry,
        'h.ws.streamer_work_queue': Queue(),
    }
