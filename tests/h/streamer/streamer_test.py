from unittest import mock

import pytest

from h.streamer import messages, streamer, websocket
from h.streamer.streamer import TOPIC_HANDLERS


class TestProcessWorkQueue:
    def test_it_sends_realtime_messages_to_messages_handle_message(
        self, process_work_queue, message, session, registry
    ):
        process_work_queue(queue=[message])

        messages.handle_message.assert_called_once_with(
            message, registry, session, topic_handlers=TOPIC_HANDLERS
        )

    def test_it_sends_websocket_messages_to_websocket_handle_message(
        self, process_work_queue, ws_message, session
    ):
        process_work_queue(queue=[ws_message])

        websocket.handle_message.assert_called_once_with(ws_message, session)

    def test_it_commits_after_each_message(
        self, process_work_queue, message, ws_message, session
    ):
        process_work_queue(queue=[message, ws_message])

        assert session.commit.call_count == 2

    def test_it_calls_close_after_commit(self, process_work_queue, session):
        process_work_queue()

        assert session.method_calls[-2:] == [mock.call.commit(), mock.call.close()]

    def test_it_rolls_back_on_handler_exception(self, process_work_queue, session):
        messages.handle_message.side_effect = RuntimeError("explosion")

        process_work_queue()

        self._assert_rollback_and_close(session)

    @pytest.mark.parametrize("exception", (KeyboardInterrupt, SystemExit))
    def test_it_reraises_certain_exceptions(
        self, process_work_queue, session, exception
    ):
        messages.handle_message.side_effect = exception

        with pytest.raises(exception):
            process_work_queue()

        self._assert_rollback_and_close(session)

    def test_it_rolls_back_on_unknown_message_type(self, process_work_queue, session):
        process_work_queue(queue=["something that is not a message"])

        self._assert_rollback_and_close(session)

    def _assert_rollback_and_close(self, session):
        session.commit.assert_not_called()
        assert session.method_calls[-2:] == [mock.call.rollback(), mock.call.close()]

    @pytest.fixture
    def process_work_queue(self, session, registry, message):
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
        db.Session.return_value = session
        return db

    @pytest.fixture(autouse=True)
    def websocket_handle_message(self, patch):
        return patch("h.streamer.websocket.handle_message")

    @pytest.fixture(autouse=True)
    def messages_handle_message(self, patch):
        return patch("h.streamer.messages.handle_message")
