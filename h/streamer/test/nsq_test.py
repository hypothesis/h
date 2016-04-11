# -*- coding: utf-8 -*-

from gevent.queue import Queue
import mock
import pytest
from pyramid import security

from h.streamer import nsq


class FakeSocket(object):
    client_id = None
    filter = None
    request = None
    terminated = None

    def __init__(self, client_id):
        self.client_id = client_id
        self.terminated = False
        self.filter = mock.MagicMock()
        self.request = mock.MagicMock()
        self.request.effective_principals = [security.Everyone]
        self.send = mock.MagicMock()


def test_handle_annotation_event_annotation_notification_format():
    """Check the format of the returned notification in the happy case."""
    message = {
        'annotation': {'permissions': {'read': ['group:__world__']}},
        'action': 'update',
        'src_client_id': 'pigeon'
    }
    socket = FakeSocket('giraffe')

    assert nsq.handle_annotation_event(message, socket) == {
        'payload': [message['annotation']],
        'type': 'annotation-notification',
        'options': {'action': 'update'},
    }


def test_handle_annotation_event_none_for_sender_socket():
    """Should return None if the socket's client_id matches the message's."""
    message = {
        'annotation': {'permissions': {'read': ['group:__world__']}},
        'action': 'update',
        'src_client_id': 'pigeon'
    }
    socket = FakeSocket('pigeon')

    assert nsq.handle_annotation_event(message, socket) is None


def test_handle_annotation_event_none_if_no_socket_filter():
    """Should return None if the socket has no filter."""
    message = {
        'annotation': {'permissions': {'read': ['group:__world__']}},
        'action': 'update',
        'src_client_id': 'pigeon'
    }
    socket = FakeSocket('giraffe')
    socket.filter = None

    assert nsq.handle_annotation_event(message, socket) is None


def test_handle_annotation_event_none_if_action_is_read():
    """Should return None if the message action is 'read'."""
    message = {
        'annotation': {'permissions': {'read': ['group:__world__']}},
        'action': 'read',
        'src_client_id': 'pigeon'
    }
    socket = FakeSocket('giraffe')

    assert nsq.handle_annotation_event(message, socket) is None


def test_handle_annotation_event_none_if_filter_does_not_match():
    """Should return None if the socket filter doesn't match the message."""
    message = {
        'annotation': {'permissions': {'read': ['group:__world__']}},
        'action': 'update',
        'src_client_id': 'pigeon'
    }
    socket = FakeSocket('giraffe')
    socket.filter.match.return_value = False

    assert nsq.handle_annotation_event(message, socket) is None


def test_handle_annotation_event_none_if_annotation_nipsad():
    """Should return None if the annotation is from a NIPSA'd user."""
    message = {
        'annotation': {
            'user': 'fred',
            'nipsa': True,
            'permissions': {'read': ['group:__world__']}
        },
        'action': 'update',
        'src_client_id': 'pigeon'
    }
    socket = FakeSocket('giraffe')

    assert nsq.handle_annotation_event(message, socket) is None


def test_handle_annotation_event_sends_nipsad_annotations_to_owners():
    """NIPSA'd users should see their own annotations."""
    message = {
        'annotation': {
            'user': 'fred',
            'nipsa': True,
            'permissions': {'read': ['group:__world__']}
        },
        'action': 'update',
        'src_client_id': 'pigeon'
    }
    socket = FakeSocket('giraffe')
    socket.request.authenticated_userid = 'fred'

    assert nsq.handle_annotation_event(message, socket) is not None


def test_handle_annotation_event_sends_if_annotation_public():
    """
    Everyone should see annotations which are public.

    When logged-out, effective principals contains only
    `pyramid.security.Everyone`. This test ensures that the system
    principal is correctly equated with the annotation principal
    'group:__world__', ensuring that everyone (including logged-out users)
    receives all public annotations.
    """
    message = {
        'annotation': {
            'user': 'fred',
            'permissions': {'read': ['group:__world__']}
        },
        'action': 'update',
        'src_client_id': 'pigeon'
    }
    socket = FakeSocket('giraffe')
    socket.request.effective_principals = [security.Everyone]

    assert nsq.handle_annotation_event(message, socket) is not None


def test_handle_annotation_event_none_if_not_in_group():
    """Users shouldn't see annotations in groups they aren't members of."""
    message = {
        'annotation': {
            'user': 'fred',
            'permissions': {'read': ['group:private-group']}
        },
        'action': 'update',
        'src_client_id': 'pigeon'
    }
    socket = FakeSocket('giraffe')
    socket.request.effective_principals = ['fred']  # No 'group:private-group'.

    assert nsq.handle_annotation_event(message, socket) is None


def test_handle_annotation_event_sends_if_in_group():
    """Users should see annotations in groups they are members of."""
    message = {
        'annotation': {
            'user': 'fred',
            'permissions': {'read': ['group:private-group']}
        },
        'action': 'update',
        'src_client_id': 'pigeon'
    }
    socket = FakeSocket('giraffe')
    socket.request.effective_principals = ['fred', 'group:private-group']

    assert nsq.handle_annotation_event(message, socket) is not None


def test_handle_user_event_sends_session_change_when_joining_or_leaving_group():
    session_model = mock.Mock()
    message = {
        'type': 'group-join',
        'userid': 'amy',
        'group': 'groupid',
        'session_model': session_model,
    }

    sock = FakeSocket('clientid')
    sock.request.authenticated_userid = 'amy'

    assert nsq.handle_user_event(message, sock) == {
        'type': 'session-change',
        'action': 'group-join',
        'model': session_model,
    }


def test_handle_user_event_none_when_socket_is_not_event_users():
    """Don't send session-change events if the event user is not the socket user."""
    message = {
        'type': 'group-join',
        'userid': 'amy',
        'group': 'groupid',
    }

    sock = FakeSocket('clientid')
    sock.request.authenticated_userid = 'bob'

    assert nsq.handle_user_event(message, sock) is None


@mock.patch('h.streamer.websocket.WebSocket')
def test_handle_message_calls_handler_once_per_socket_with_deserialized_message(websocket):
    handler = mock.Mock(return_value=None)
    message = nsq.Message(topic='foo', payload='{"foo": "bar"}')
    websocket.instances = [FakeSocket('a'), FakeSocket('b')]

    nsq.handle_message(message, topic_handlers={'foo': handler})

    assert handler.mock_calls == [
        mock.call({'foo': 'bar'}, websocket.instances[0]),
        mock.call({'foo': 'bar'}, websocket.instances[1]),
    ]


@mock.patch('h.streamer.websocket.WebSocket')
def test_handle_message_sends_serialized_messages_down_websocket(websocket):
    handler = mock.Mock(return_value={'just': 'some message'})
    message = nsq.Message(topic='foo', payload='{"foo": "bar"}')
    socket = FakeSocket('a')
    websocket.instances = [socket]

    nsq.handle_message(message, topic_handlers={'foo': handler})

    socket.send.assert_called_once_with('{"just": "some message"}')


@mock.patch('h.streamer.websocket.WebSocket')
def test_handle_message_does_not_send_messages_down_websocket_if_handler_response_is_none(websocket):
    handler = mock.Mock(return_value=None)
    message = nsq.Message(topic='foo', payload='{"foo": "bar"}')
    socket = FakeSocket('a')
    websocket.instances = [socket]

    nsq.handle_message(message, topic_handlers={'foo': handler})

    assert socket.send.call_count == 0


@mock.patch('h.streamer.websocket.WebSocket')
def test_handle_message_does_not_send_messages_down_websocket_if_socket_terminated(websocket):
    handler = mock.Mock(return_value={'just': 'some message'})
    message = nsq.Message(topic='foo', payload='{"foo": "bar"}')
    socket = FakeSocket('a')
    socket.terminated = True
    websocket.instances = [socket]

    nsq.handle_message(message, topic_handlers={'foo': handler})

    assert socket.send.call_count == 0


@mock.patch('h.sentry')
def test_process_nsq_topic_creates_sentry_client(fake_sentry, get_reader):
    settings = {}
    queue = Queue()

    nsq.process_nsq_topic(settings, 'donkeys', queue, raise_error=False)

    fake_sentry.get_client.assert_called_once_with(settings)


def test_process_nsq_topic_creates_reader_for_topic(get_reader):
    settings = {}
    queue = Queue()

    nsq.process_nsq_topic(settings, 'donkeys', queue, raise_error=False)

    get_reader.assert_any_call(settings, 'donkeys', mock.ANY,
                               sentry_client=mock.ANY)


def test_process_nsq_topic_connects_reader_on_message_to_handle_message(get_reader):
    settings = {}
    queue = Queue()
    message = mock.Mock(body='hello')
    reader = get_reader.return_value
    reader.topic = 'donkeys'

    nsq.process_nsq_topic(settings, 'donkeys', queue, raise_error=False)
    message_handler = reader.on_message.connect.call_args[1]['receiver']
    message_handler(reader, message)
    result = queue.get_nowait()

    assert result.topic == 'donkeys'
    assert result.payload == 'hello'


def test_process_nsq_topic_starts_reader(get_reader):
    settings = {}
    reader = get_reader.return_value
    queue = Queue()

    nsq.process_nsq_topic(settings, 'donkeys', queue, raise_error=False)

    reader.start.assert_called_once_with()


def test_process_nsq_topic_joins_reader(get_reader):
    settings = {}
    reader = get_reader.return_value
    queue = Queue()

    nsq.process_nsq_topic(settings, 'gorillas', queue, raise_error=False)

    reader.join.assert_called_once_with(raise_error=False)


def test_process_nsq_topic_raises_if_reader_exits_early(get_reader):
    settings = {}
    reader = get_reader.return_value
    queue = Queue()

    with pytest.raises(RuntimeError):
        nsq.process_nsq_topic(settings, 'gorillas', queue)

    reader.join.assert_called_once_with(raise_error=True)


@pytest.fixture
def get_reader(patch):
    return patch('h.queue.get_reader')
