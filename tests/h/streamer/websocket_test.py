import json
from collections import namedtuple
from unittest import mock

import pytest
from gevent.queue import Queue
from h_matchers import Any
from jsonschema import ValidationError

from h.security import Identity
from h.streamer import websocket

FakeMessage = namedtuple("FakeMessage", ["data"])


class TestMessage:
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


class TestWebSocket:
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

    @pytest.mark.parametrize("debug", (True, False))
    def test_invalid_incoming_message_closes_connection(
        self, client, fake_socket_close, debug
    ):
        """Invalid messages should cause termination of the connection."""
        client.debug = debug
        message = FakeMessage('{"foo":missingquotes}')

        client.received_message(message)

        fake_socket_close.assert_called_once_with(
            client, reason="invalid message format"
        )

    def test_socket_sets_auth_data_from_environ(self, client, fake_environ):
        assert client.identity == fake_environ["h.ws.identity"]

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

    def test_debug_mode(self, fake_environ, log):
        sock = mock.Mock(spec_set=["sendall"])
        fake_environ["h.ws.debug"] = True
        client = websocket.WebSocket(sock, environ=fake_environ)

        message = FakeMessage(json.dumps({"type": "whoami", "id": 1}))
        log.info.reset_mock()

        client.received_message(message)
        client.send_json({"type": "whoyouare", "ok": True, "reply_to": 1})
        client.closed(code=1006, reason="Client went away")

        assert len(log.info.mock_calls) == 3

    @pytest.fixture(autouse=True)
    def with_no_socket_instances(self):
        # The instances set is automatically populated when web sockets are
        # created and can couple different tests together
        websocket.WebSocket.instances.clear()

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
            "h.ws.debug": False,
            "h.ws.identity": Identity(),
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
class TestHandleMessage:
    def test_uses_unknown_handler_for_missing_type(self, socket, unknown_handler):
        """If the type is missing, call the `None` handler."""
        message = websocket.Message(socket, payload={"foo": "bar"})

        websocket.handle_message(message)

        unknown_handler.assert_called_once_with(message, session=None)

    def test_uses_unknown_handler_for_unknown_type(self, socket, unknown_handler):
        """If the type is unknown, call the `None` handler."""
        message = websocket.Message(socket, payload={"type": "donkeys", "foo": "bar"})

        websocket.handle_message(message)

        unknown_handler.assert_called_once_with(message, session=None)

    def test_uses_appropriate_handler_for_known_type(self, socket, foo_handler):
        """If the type is recognised, call the relevant handler."""
        message = websocket.Message(socket, payload={"type": "foo", "foo": "bar"})

        websocket.handle_message(message)

        foo_handler.assert_called_once_with(message, session=None)

    def test_debug_mode(self, socket, log):
        socket.debug = True
        message = websocket.Message(socket, payload={"type": "foo", "foo": "bar"})
        websocket.handle_message(message)
        log.info.assert_called_once()

    @pytest.fixture
    def foo_handler(self):
        return mock.Mock(spec_set=[])

    @pytest.fixture
    def unknown_handler(self):
        return mock.Mock(spec_set=[])

    @pytest.fixture
    def socket(self):
        return mock.create_autospec(websocket.WebSocket, instance=True, spec_set=True)

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


class TestHandleClientIDMessage:
    def test_sets_client_id(self, socket):
        """Updates the socket client_id if valid."""
        message = websocket.Message(
            socket=socket, payload={"messageType": "client_id", "value": "abcd1234"}
        )

        websocket.handle_client_id_message(message)

        assert socket.client_id == "abcd1234"

    def test_missing_value_error(self, socket):
        message = websocket.Message(socket=socket, payload={"messageType": "client_id"})

        with mock.patch.object(websocket.Message, "reply") as mock_reply:
            websocket.handle_client_id_message(message)

        mock_reply.assert_called_once_with(Any.dict.containing(["error"]), ok=False)

    @pytest.fixture
    def socket(self, socket):
        socket.client_id = None
        return socket


class TestHandleFilterMessage:
    def test_sets_socket_filter(self, socket, SocketFilter):
        filter_ = {
            "actions": {},
            "match_policy": "include_any",
            "clauses": [
                {"field": "/uri", "operator": "equals", "value": "http://example.com"}
            ],
        }

        message = websocket.Message(socket=socket, payload={"filter": filter_})

        websocket.handle_filter_message(message)

        SocketFilter.set_filter.assert_called_once_with(socket, filter_)

    def test_missing_filter_error(self, socket):
        message = websocket.Message(socket=socket, payload={"type": "filter"})

        with mock.patch.object(websocket.Message, "reply") as mock_reply:
            websocket.handle_filter_message(message)

        mock_reply.assert_called_once_with(Any.dict.containing(["error"]), ok=False)

    @mock.patch("h.streamer.websocket.jsonschema.validate")
    def test_invalid_filter_error(self, validate, socket):
        message = websocket.Message(
            socket=socket, payload={"type": "filter", "filter": {"wibble": "giraffe"}}
        )
        validate.side_effect = ValidationError("kaboom!")

        with mock.patch.object(websocket.Message, "reply") as mock_reply:
            websocket.handle_filter_message(message)

        mock_reply.assert_called_once_with(Any.dict.containing(["error"]), ok=False)

    @pytest.fixture
    def SocketFilter(self, patch):
        return patch("h.streamer.websocket.SocketFilter")

    @pytest.fixture
    def socket(self, socket):
        socket.filter = None
        return socket


class TestHandlePingMessage:
    def test_pong(self):
        message = websocket.Message(
            socket=mock.sentinel.socket, payload={"type": "ping"}
        )

        with mock.patch.object(websocket.Message, "reply") as mock_reply:
            websocket.handle_ping_message(message)

        mock_reply.assert_called_once_with({"type": "pong"})


class TestHandleWhoamiMessage:
    @pytest.mark.parametrize("with_identity", (True, False))
    def test_replies_with_whoyouare_message(self, socket, with_identity):
        if not with_identity:
            socket.identity = False

        message = websocket.Message(socket=socket, payload={"type": "whoami"})

        with mock.patch.object(websocket.Message, "reply") as mock_reply:
            websocket.handle_whoami_message(message)

        mock_reply.assert_called_once_with(
            {
                "type": "whoyouare",
                "userid": socket.identity.user.userid if with_identity else None,
            }
        )


class TestUnknownMessage:
    def test_error(self):
        message = websocket.Message(
            socket=mock.sentinel.socket, payload={"type": "wibble"}
        )

        with mock.patch.object(websocket.Message, "reply") as mock_reply:
            websocket.handle_unknown_message(message)

        mock_reply.assert_called_once_with(Any.dict.containing(["error"]), ok=False)


@pytest.fixture
def log(patch):
    return patch("h.streamer.websocket.log")
