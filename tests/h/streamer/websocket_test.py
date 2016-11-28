# -*- coding: utf-8 -*-

from collections import namedtuple

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


def test_socket_send_json(fake_environ, fake_json, fake_socket_send):
    socket = mock.Mock()
    client = websocket.WebSocket(socket, environ=fake_environ)

    payload = {'foo': 'bar'}
    client.send_json(payload)

    fake_json.dumps.assert_called_once_with(payload)
    fake_socket_send.assert_called_once_with(client, fake_json.dumps.return_value)


def test_socket_send_json_skips_when_terminated(fake_environ, fake_json, fake_socket_send, fake_socket_terminated):
    socket = mock.Mock()
    client = websocket.WebSocket(socket, environ=fake_environ)

    fake_socket_terminated.return_value = True
    client.send_json({'foo': 'bar'})

    assert not fake_json.dumps.called
    assert not fake_socket_send.called


@pytest.mark.usefixtures('handlers')
class TestHandleMessage(object):

    def test_closes_connection_for_invalid_json(self):
        """If we receive invalid JSON, we close the connection."""
        socket = mock.Mock(spec_set=['close'])
        message = websocket.Message(socket, payload='gibberish')

        websocket.handle_message(message)

        socket.close.assert_called_once_with(reason='invalid message format')

    def test_uses_unknown_handler_for_missing_type(self, unknown_handler):
        """If the type is missing, call the `None` handler."""
        socket = mock.Mock(spec_set=['close'])
        message = websocket.Message(socket, payload='{"foo":"bar"}')

        websocket.handle_message(message)

        unknown_handler.assert_called_once_with(socket,
                                                {"foo": "bar"},
                                                session=None)

    def test_uses_unknown_handler_for_unknown_type(self, unknown_handler):
        """If the type is unknown, call the `None` handler."""
        socket = mock.Mock(spec_set=['close'])
        message = websocket.Message(socket, payload='{"type":"donkeys","foo":"bar"}')

        websocket.handle_message(message)

        unknown_handler.assert_called_once_with(socket,
                                                {"type": "donkeys",
                                                 "foo": "bar"},
                                                session=None)

    def test_uses_appropriate_handler_for_known_type(self, foo_handler):
        """If the type is recognised, call the relevant handler."""
        socket = mock.Mock(spec_set=['close'])
        message = websocket.Message(socket, payload='{"type":"foo","foo":"bar"}')

        websocket.handle_message(message)

        foo_handler.assert_called_once_with(socket,
                                            {"type": "foo", "foo": "bar"},
                                            session=None)

    @pytest.fixture
    def foo_handler(self):
        return mock.Mock(spec_set=[])

    @pytest.fixture
    def unknown_handler(self):
        return mock.Mock(spec_set=[])

    @pytest.fixture
    def handlers(self, request, foo_handler, unknown_handler):
        patcher = mock.patch.dict('h.streamer.websocket.MESSAGE_HANDLERS', {
            'foo': foo_handler,
            None: unknown_handler,
        }, clear=True)
        handlers = patcher.start()
        request.addfinalizer(patcher.stop)
        return handlers


def test_handle_client_id_message_sets_socket_client_id_for_client_id_messages():
    socket = mock.Mock()
    socket.client_id = None
    payload = {
        'messageType': 'client_id',
        'value': 'abcd1234',
    }

    websocket.handle_client_id_message(socket, payload)

    assert socket.client_id == 'abcd1234'


def test_handle_message_sets_socket_filter_for_filter_messages():
    socket = mock.Mock()
    socket.filter = None
    payload = {
        'filter': {
            'actions': {},
            'match_policy': 'include_all',
            'clauses': [{
                'field': '/uri',
                'operator': 'equals',
                'value': 'http://example.com',
            }],
        }
    }

    websocket.handle_filter_message(socket, payload)

    assert socket.filter is not None


@mock.patch('memex.storage.expand_uri')
def test_handle_filter_message_expands_uris_in_uri_filter_with_session(expand_uri):
    expand_uri.return_value = ['http://example.com',
                               'http://example.com/alter',
                               'http://example.com/print']
    session = mock.sentinel.db_session
    socket = mock.Mock()
    socket.filter = None
    payload = {
        'filter': {
            'actions': {},
            'match_policy': 'include_all',
            'clauses': [{
                'field': '/uri',
                'operator': 'equals',
                'value': 'http://example.com',
            }],
        }
    }

    websocket.handle_filter_message(socket, payload, session=session)

    uri_filter = socket.filter.filter['clauses'][0]
    uri_values = uri_filter['value']
    assert len(uri_values) == 3
    assert 'http://example.com' in uri_values
    assert 'http://example.com/alter' in uri_values
    assert 'http://example.com/print' in uri_values


@mock.patch('memex.storage.expand_uri')
def test_handle_message_expands_uris_using_passed_session(expand_uri):
    expand_uri.return_value = ['http://example.com', 'http://example.org/']
    session = mock.sentinel.db_session
    socket = mock.Mock()
    socket.filter = None
    payload = {
        'filter': {
            'actions': {},
            'match_policy': 'include_all',
            'clauses': [{
                'field': '/uri',
                'operator': 'equals',
                'value': 'http://example.com',
            }],
        }
    }

    websocket.handle_filter_message(socket, payload, session=session)

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


@pytest.fixture
def fake_json(patch):
    return patch('h.streamer.websocket.json')


@pytest.fixture
def fake_socket_send(patch):
    return patch('h.streamer.websocket.WebSocket.send')


@pytest.fixture
def fake_socket_terminated(patch):
    return patch('h.streamer.websocket.WebSocket.terminated')
