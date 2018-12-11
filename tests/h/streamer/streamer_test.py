# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import mock
from mock import call
import pytest

from h.streamer import messages
from h.streamer import streamer
from h.streamer import websocket


def test_process_work_queue_sends_realtime_messages_to_messages_handle_message(session):
    message = messages.Message(topic="foo", payload="bar")
    queue = [message]
    settings = {"foo": "bar"}

    streamer.process_work_queue(settings, queue, session_factory=lambda _: session)

    messages.handle_message.assert_called_once_with(
        message, settings, session, topic_handlers=mock.ANY
    )


def test_process_work_queue_uses_appropriate_topic_handlers_for_realtime_messages(
    session
):
    message = messages.Message(topic="user", payload="bar")
    queue = [message]
    settings = {"foo": "bar"}

    streamer.process_work_queue(settings, queue, session_factory=lambda _: session)

    topic_handlers = {
        "annotation": messages.handle_annotation_event,
        "user": messages.handle_user_event,
    }

    messages.handle_message.assert_called_once_with(
        mock.ANY, settings, session, topic_handlers=topic_handlers
    )


def test_process_work_queue_sends_websocket_messages_to_websocket_handle_message(
    session
):
    message = websocket.Message(socket=mock.sentinel.SOCKET, payload="bar")
    queue = [message]

    streamer.process_work_queue({}, queue, session_factory=lambda _: session)

    websocket.handle_message.assert_called_once_with(message, session)


def test_process_work_queue_commits_after_each_message(session):
    message1 = websocket.Message(socket=mock.sentinel.SOCKET, payload="bar")
    message2 = messages.Message(topic="user", payload="bar")
    queue = [message1, message2]

    streamer.process_work_queue({}, queue, session_factory=lambda _: session)

    assert session.commit.call_count == 2


def test_process_work_queue_rolls_back_on_handler_exception(session):
    message = messages.Message(topic="foo", payload="bar")
    queue = [message]

    messages.handle_message.side_effect = RuntimeError("explosion")

    streamer.process_work_queue({}, queue, session_factory=lambda _: session)

    session.commit.assert_not_called()
    session.rollback.assert_called_once_with()


def test_process_work_queue_rolls_back_on_unknown_message_type(session):
    message = "something that is not a message"
    queue = [message]

    streamer.process_work_queue({}, queue, session_factory=lambda _: session)

    session.commit.assert_not_called()
    session.rollback.assert_called_once_with()


def test_process_work_queue_calls_close_after_commit(session):
    message = messages.Message(topic="annotation", payload="bar")
    queue = [message]

    streamer.process_work_queue({}, queue, session_factory=lambda _: session)

    assert session.method_calls[-2:] == [call.commit(), call.close()]


def test_process_work_queue_calls_close_after_rollback(session):
    message = messages.Message(topic="foo", payload="bar")
    queue = [message]

    messages.handle_message.side_effect = RuntimeError("explosion")

    streamer.process_work_queue({}, queue, session_factory=lambda _: session)

    assert session.method_calls[-2:] == [call.rollback(), call.close()]


@pytest.fixture
def session():
    return mock.Mock(spec_set=["close", "commit", "execute", "rollback"])


@pytest.fixture(autouse=True)
def websocket_handle_message(patch):
    return patch("h.streamer.websocket.handle_message")


@pytest.fixture(autouse=True)
def messages_handle_message(patch):
    return patch("h.streamer.messages.handle_message")
