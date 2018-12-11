# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from collections import namedtuple

import mock
import pytest
from gevent.queue import Queue
from jsonschema import ValidationError
from pyramid import security

from h.streamer import websocket


FakeMessage = namedtuple("FakeMessage", ["data"])


class TestMessage(object):
    def test_reply_adds_reply_to(self, socket):
        """Adds an appropriate `reply_to` field to the sent message."""
        message = websocket.Message(socket=socket, payload={"id": 123})

        message.reply({"foo": "bar"})

        socket.send_json.assert_called_once_with(
            {"ok": True, "reply_to": 123, "foo": "bar"}
        )

    @pytest.mark.parametrize("ok", [True, False])
    def test_reply_adds_ok(self, ok, socket):
        """Adds an appropriate `ok` field to the sent message."""
        message = websocket.Message(socket=socket, payload={"id": 123})

        message.reply({"foo": "bar"}, ok=ok)

        socket.send_json.assert_called_once_with(
            {"ok": ok, "reply_to": 123, "foo": "bar"}
        )

    def test_reply_overrides_ok_and_reply_to_fields_in_payload(self, socket):
        """Payload `ok` and `reply_to` fields should be ignored."""
        message = websocket.Message(socket=socket, payload={"id": 123})

        message.reply({"foo": "bar", "ok": False, "reply_to": "wibble"})

        socket.send_json.assert_called_once_with(
            {"ok": True, "reply_to": 123, "foo": "bar"}
        )

    @pytest.mark.parametrize(
        "payload", [{}, {"id": "a string"}, {"id": [1, 2, 3]}, {"id": None}]
    )
    def test_reply_does_not_send_if_id_missing_or_invalid(self, payload, socket):
        """Do not send a reply at all if we don't have an incoming message ID."""
        message = websocket.Message(socket=socket, payload=payload)

        message.reply({"foo": "bar"})

        assert not socket.send_json.called

    @pytest.fixture
    def socket(self):
        return mock.Mock(spec_set=["send_json"])


class TestWebSocket(object):
    def test_stores_instance_list(self, fake_environ):
        clients = [
            websocket.WebSocket(mock.sentinel.sock1, environ=fake_environ),
            websocket.WebSocket(mock.sentinel.sock2, environ=fake_environ),
        ]

        for c in clients:
            assert c in websocket.WebSocket.instances

    def test_removes_self_from_instance_list_when_closed(self, fake_environ):
        client1 = websocket.WebSocket(mock.sentinel.sock1, environ=fake_environ)
        client2 = websocket.WebSocket(mock.sentinel.sock2, environ=fake_environ)

        assert len(websocket.WebSocket.instances) == 2
        client1.closed(1000)
        assert client1 not in websocket.WebSocket.instances
        client2.closed(1000)
        assert client2 not in websocket.WebSocket.instances

        # A second closure (however unusual) should not raise
        client1.closed(1000)

    def test_enqueues_incoming_messages(self, client, queue):
        """Valid messages are pushed onto the queue."""
        message = FakeMessage('{"foo":"bar"}')

        client.received_message(message)
        result = queue.get_nowait()

        assert result

    def test_enqueued_message_has_reference_to_client(self, client, queue):
        """Valid messages should have a backreference to the instance."""
        message = FakeMessage('{"foo":"bar"}')

        client.received_message(message)
        result = queue.get_nowait()

        assert result.socket == client

    def test_enqueued_message_has_parsed_payload(self, client, queue):
        """Valid messages should have a parsed payload."""
        message = FakeMessage('{"foo":"bar"}')

        client.received_message(message)
        result = queue.get_nowait()

        assert result.payload == {"foo": "bar"}

    def test_invalid_incoming_message_not_queued(self, client, queue):
        """Invalid messages should not end up on the queue."""
        message = FakeMessage('{"foo":missingquotes}')

        client.received_message(message)

        assert queue.empty()

    def test_invalid_incoming_message_closes_connection(
        self, client, queue, fake_socket_close
    ):
        """Invalid messages should cause termination of the connection."""
        message = FakeMessage('{"foo":missingquotes}')

        client.received_message(message)

        fake_socket_close.assert_called_once_with(
            client, reason="invalid message format"
        )

    def test_socket_sets_auth_data_from_environ(self, client):
        assert client.authenticated_userid == "janet"
        assert client.effective_principals == [
            security.Everyone,
            security.Authenticated,
            "group:__world__",
        ]

    def test_socket_sets_registry_from_environ(self, client):
        assert client.registry == mock.sentinel.registry

    def test_socket_send_json(self, client, fake_socket_send):
        payload = {"foo": "bar"}

        client.send_json(payload)

        fake_socket_send.assert_called_once_with(client, '{"foo": "bar"}')

    def test_socket_send_json_skips_when_terminated(
        self, client, fake_socket_send, fake_socket_terminated
    ):
        fake_socket_terminated.return_value = True

        client.send_json({"foo": "bar"})

        assert not fake_socket_send.called

    @pytest.fixture
    def client(self, fake_environ):
        sock = mock.Mock(spec_set=["sendall"])
        return websocket.WebSocket(sock, environ=fake_environ)

    @pytest.fixture
    def queue(self):
        return Queue()

    @pytest.fixture
    def fake_environ(self, queue):
        return {
            "h.ws.authenticated_userid": "janet",
            "h.ws.effective_principals": [
                security.Everyone,
                security.Authenticated,
                "group:__world__",
            ],
            "h.ws.registry": mock.sentinel.registry,
            "h.ws.streamer_work_queue": queue,
        }

    @pytest.fixture
    def fake_socket_close(self, patch):
        return patch("h.streamer.websocket.WebSocket.close")

    @pytest.fixture
    def fake_socket_send(self, patch):
        return patch("h.streamer.websocket.WebSocket.send")

    @pytest.fixture
    def fake_socket_terminated(self, patch):
        return patch("h.streamer.websocket.WebSocket.terminated")


@pytest.mark.usefixtures("handlers")
class TestHandleMessage(object):
    def test_uses_unknown_handler_for_missing_type(self, unknown_handler):
        """If the type is missing, call the `None` handler."""
        socket = mock.Mock(spec_set=["close"])
        message = websocket.Message(socket, payload={"foo": "bar"})

        websocket.handle_message(message)

        unknown_handler.assert_called_once_with(message, session=None)

    def test_uses_unknown_handler_for_unknown_type(self, unknown_handler):
        """If the type is unknown, call the `None` handler."""
        socket = mock.Mock(spec_set=["close"])
        message = websocket.Message(socket, payload={"type": "donkeys", "foo": "bar"})

        websocket.handle_message(message)

        unknown_handler.assert_called_once_with(message, session=None)

    def test_uses_appropriate_handler_for_known_type(self, foo_handler):
        """If the type is recognised, call the relevant handler."""
        socket = mock.Mock(spec_set=["close"])
        message = websocket.Message(socket, payload={"type": "foo", "foo": "bar"})

        websocket.handle_message(message)

        foo_handler.assert_called_once_with(message, session=None)

    @pytest.fixture
    def foo_handler(self):
        return mock.Mock(spec_set=[])

    @pytest.fixture
    def unknown_handler(self):
        return mock.Mock(spec_set=[])

    @pytest.fixture
    def handlers(self, request, foo_handler, unknown_handler):
        patcher = mock.patch.dict(
            "h.streamer.websocket.MESSAGE_HANDLERS",
            {"foo": foo_handler, None: unknown_handler},
            clear=True,
        )
        handlers = patcher.start()
        request.addfinalizer(patcher.stop)
        return handlers


class TestHandleClientIDMessage(object):
    def test_sets_client_id(self, socket):
        """Updates the socket client_id if valid."""
        message = websocket.Message(
            socket=socket, payload={"messageType": "client_id", "value": "abcd1234"}
        )

        websocket.handle_client_id_message(message)

        assert socket.client_id == "abcd1234"

    def test_missing_value_error(self, matchers, socket):
        message = websocket.Message(socket=socket, payload={"messageType": "client_id"})

        with mock.patch.object(websocket.Message, "reply") as mock_reply:
            websocket.handle_client_id_message(message)

        mock_reply.assert_called_once_with(
            matchers.MappingContaining("error"), ok=False
        )

    @pytest.fixture
    def socket(self):
        socket = mock.Mock()
        socket.client_id = None
        return socket


class TestHandleFilterMessage(object):
    def test_sets_socket_filter(self, socket):
        message = websocket.Message(
            socket=socket,
            payload={
                "filter": {
                    "actions": {},
                    "match_policy": "include_any",
                    "clauses": [
                        {
                            "field": "/uri",
                            "operator": "equals",
                            "value": "http://example.com",
                        }
                    ],
                }
            },
        )

        websocket.handle_filter_message(message)

        assert socket.filter is not None

    @mock.patch("h.streamer.websocket.storage.expand_uri")
    def test_expands_uris_in_uri_filter_with_session(self, expand_uri, socket):
        expand_uri.return_value = [
            "http://example.com",
            "http://example.com/alter",
            "http://example.com/print",
        ]
        session = mock.sentinel.db_session
        message = websocket.Message(
            socket=socket,
            payload={
                "filter": {
                    "actions": {},
                    "match_policy": "include_any",
                    "clauses": [
                        {
                            "field": "/uri",
                            "operator": "equals",
                            "value": "http://example.com",
                        }
                    ],
                }
            },
        )

        websocket.handle_filter_message(message, session=session)

        uri_filter = socket.filter.filter["clauses"][0]
        uri_values = uri_filter["value"]
        assert len(uri_values) == 3
        assert "http://example.com" in uri_values
        assert "http://example.com/alter" in uri_values
        assert "http://example.com/print" in uri_values

    @mock.patch("h.streamer.websocket.storage.expand_uri")
    def test_expands_uris_using_passed_session(self, expand_uri, socket):
        expand_uri.return_value = ["http://example.com", "http://example.org/"]
        session = mock.sentinel.db_session
        message = websocket.Message(
            socket=socket,
            payload={
                "filter": {
                    "actions": {},
                    "match_policy": "include_any",
                    "clauses": [
                        {
                            "field": "/uri",
                            "operator": "equals",
                            "value": "http://example.com",
                        }
                    ],
                }
            },
        )

        websocket.handle_filter_message(message, session=session)

        expand_uri.assert_called_once_with(session, "http://example.com")

    def test_missing_filter_error(self, matchers, socket):
        message = websocket.Message(socket=socket, payload={"type": "filter"})

        with mock.patch.object(websocket.Message, "reply") as mock_reply:
            websocket.handle_filter_message(message)

        mock_reply.assert_called_once_with(
            matchers.MappingContaining("error"), ok=False
        )

    @mock.patch("h.streamer.websocket.jsonschema.validate")
    def test_invalid_filter_error(self, validate, matchers, socket):
        message = websocket.Message(
            socket=socket, payload={"type": "filter", "filter": {"wibble": "giraffe"}}
        )
        validate.side_effect = ValidationError("kaboom!")

        with mock.patch.object(websocket.Message, "reply") as mock_reply:
            websocket.handle_filter_message(message)

        mock_reply.assert_called_once_with(
            matchers.MappingContaining("error"), ok=False
        )

    @pytest.fixture
    def socket(self):
        socket = mock.Mock()
        socket.filter = None
        return socket


class TestHandlePingMessage(object):
    def test_pong(self):
        message = websocket.Message(
            socket=mock.sentinel.socket, payload={"type": "ping"}
        )

        with mock.patch.object(websocket.Message, "reply") as mock_reply:
            websocket.handle_ping_message(message)

        mock_reply.assert_called_once_with({"type": "pong"})


class TestHandleWhoamiMessage(object):
    @pytest.mark.parametrize("userid", [None, "acct:foo@example.com"])
    def test_replies_with_whoyouare_message(self, socket, userid):
        """Send back a `whoyouare` message with a userid (which may be null)."""
        socket.authenticated_userid = userid
        message = websocket.Message(socket=socket, payload={"type": "whoami"})

        with mock.patch.object(websocket.Message, "reply") as mock_reply:
            websocket.handle_whoami_message(message)

        mock_reply.assert_called_once_with({"type": "whoyouare", "userid": userid})

    @pytest.fixture
    def socket(self):
        socket = mock.Mock()
        socket.authenticated_userid = None
        return socket


class TestUnknownMessage(object):
    def test_error(self, matchers):
        message = websocket.Message(
            socket=mock.sentinel.socket, payload={"type": "wibble"}
        )

        with mock.patch.object(websocket.Message, "reply") as mock_reply:
            websocket.handle_unknown_message(message)

        mock_reply.assert_called_once_with(
            matchers.MappingContaining("error"), ok=False
        )
