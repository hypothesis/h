# -*- coding: utf-8 -*-

import mock
from mock import call
import pytest

from h.streamer import nsq
from h.streamer import streamer
from h.streamer import websocket


def test_process_work_queue_sends_nsq_messages_to_nsq_handle_message(session):
    message = nsq.Message(topic='foo', payload='bar')
    queue = [message]

    streamer.process_work_queue({}, queue, session_factory=lambda: session)

    nsq.handle_message.assert_called_once_with(message,
                                               topic_handlers=mock.ANY)


def test_process_work_queue_uses_appropriate_topic_handlers_for_nsq_messages(session):
    message = nsq.Message(topic='foo', payload='bar')
    queue = [message]

    streamer.process_work_queue({'nsq.namespace': 'wibble'},
                                queue,
                                session_factory=lambda: session)

    topic_handlers = {
        'wibble-annotations': nsq.handle_annotation_event,
        'wibble-user': nsq.handle_user_event,
    }

    nsq.handle_message.assert_called_once_with(mock.ANY,
                                               topic_handlers=topic_handlers)


def test_process_work_queue_sends_websocket_messages_to_websocket_handle_message(session):
    message = websocket.Message(socket=mock.sentinel.SOCKET, payload='bar')
    queue = [message]

    streamer.process_work_queue({}, queue, session_factory=lambda: session)

    websocket.handle_message.assert_called_once_with(message)


def test_process_work_queue_commits_after_each_message(session):
    message1 = websocket.Message(socket=mock.sentinel.SOCKET, payload='bar')
    message2 = nsq.Message(topic='foo', payload='bar')
    queue = [message1, message2]

    streamer.process_work_queue({}, queue, session_factory=lambda: session)

    assert session.commit.call_count == 2


def test_process_work_queue_rolls_back_on_handler_exception(session):
    message = nsq.Message(topic='foo', payload='bar')
    queue = [message]

    nsq.handle_message.side_effect = RuntimeError('explosion')

    streamer.process_work_queue({}, queue, session_factory=lambda: session)

    session.commit.assert_not_called()
    session.rollback.assert_called_once_with()


def test_process_work_queue_rolls_back_on_unknown_message_type(session):
    message = 'something that is not a message'
    queue = [message]

    streamer.process_work_queue({}, queue, session_factory=lambda: session)

    session.commit.assert_not_called()
    session.rollback.assert_called_once_with()


def test_process_work_queue_calls_close_after_commit(session):
    message = nsq.Message(topic='foo', payload='bar')
    queue = [message]

    streamer.process_work_queue({}, queue, session_factory=lambda: session)

    assert session.method_calls[-2:] == [
        call.commit(),
        call.close()
    ]


def test_process_work_queue_calls_close_after_rollback(session):
    message = nsq.Message(topic='foo', payload='bar')
    queue = [message]

    nsq.handle_message.side_effect = RuntimeError('explosion')

    streamer.process_work_queue({}, queue, session_factory=lambda: session)

    assert session.method_calls[-2:] == [
        call.rollback(),
        call.close()
    ]


@pytest.fixture
def session():
    return mock.Mock(spec_set=['close', 'commit', 'execute', 'rollback'])


@pytest.fixture(autouse=True)
def nsq_handle_message(patch):
    return patch('h.streamer.nsq.handle_message')


@pytest.fixture(autouse=True)
def websocket_handle_message(patch):
    return patch('h.streamer.websocket.handle_message')
