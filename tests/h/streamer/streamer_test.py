from unittest import mock

import pytest

from h.streamer import messages, streamer, websocket
from h.streamer.streamer import TOPIC_HANDLERS, UnknownMessageType


class TestProcessWorkQueue:
    def test_it_sends_realtime_messages_to_messages_handle_message(
        self, process_work_queue, message, session, registry
    ):
        process_work_queue(queue=[message])

        messages.handle_message.assert_called_once_with(  # pylint:disable=no-member
            message,
            registry,
            session,
            topic_handlers=TOPIC_HANDLERS,
        )

    def test_it_sends_websocket_messages_to_websocket_handle_message(
        self, process_work_queue, ws_message, session
    ):
        process_work_queue(queue=[ws_message])

        websocket.handle_message.assert_called_once_with(  # pylint:disable=no-member
            ws_message, session
        )

    def test_it_raises_UnknownMessageType_for_strange_messages(
        self, process_work_queue
    ):
        # Technically we don't actually raise in practice, as the transaction
        # wrapper will catch it
        with pytest.raises(UnknownMessageType):
            process_work_queue(queue=["not a message"])

    def test_it_wraps_each_message_in_a_transaction(
        self, process_work_queue, message, db
    ):
        messages = [message] * 3

        process_work_queue(queue=messages)

        context_manager = db.read_only_transaction.return_value
        assert context_manager.__enter__.call_count == len(messages)
        assert context_manager.__exit__.call_count == len(messages)

    @pytest.fixture
    def process_work_queue(self, registry, message):
        def process_work_queue(queue=None):
            return streamer.process_work_queue(registry, queue or [message])

        return process_work_queue

    @pytest.fixture
    def message(self):
        return messages.Message(topic="foo", payload="bar")

    @pytest.fixture
    def ws_message(self):
        return websocket.Message(socket=mock.sentinel.SOCKET, payload="bar")

    @pytest.fixture
    def registry(self, pyramid_request):
        return pyramid_request.registry

    @pytest.fixture
    def session(self):
        return mock.Mock(spec_set=["close", "commit", "execute", "rollback"])

    @pytest.fixture(autouse=True)
    def db(self, patch, session):
        db = patch("h.streamer.streamer.db")
        db.get_session.return_value = session
        return db

    @pytest.fixture(autouse=True)
    def websocket_handle_message(self, patch):
        return patch("h.streamer.websocket.handle_message")

    @pytest.fixture(autouse=True)
    def messages_handle_message(self, patch):
        return patch("h.streamer.messages.handle_message")
