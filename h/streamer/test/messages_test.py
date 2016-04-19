from gevent.queue import Queue
import mock
from pyramid import security
import pytest

from h.streamer import messages


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


class TestProcessMessages(object):
    def test_creates_sentry_client(self, fake_sentry, fake_consumer, queue):
        settings = {}

        messages.process_messages(settings, 'foobar', queue, raise_error=False)

        fake_sentry.get_client.assert_called_once_with(settings)

    def test_passes_sentry_client_to_consumer(self, fake_sentry, fake_consumer, queue):
        messages.process_messages({}, 'foobar', queue, raise_error=False)

        fake_consumer.assert_called_once_with(connection=mock.ANY,
                                              routing_key=mock.ANY,
                                              handler=mock.ANY,
                                              sentry_client=fake_sentry.get_client.return_value)

    def test_passes_routing_key_to_consumer(self, fake_consumer, queue):
        messages.process_messages({}, 'foobar', queue, raise_error=False)

        fake_consumer.assert_called_once_with(connection=mock.ANY,
                                              routing_key='foobar',
                                              handler=mock.ANY,
                                              sentry_client=mock.ANY)

    def test_initializes_new_connection(self, fake_realtime, fake_consumer, queue):
        settings = {}
        messages.process_messages(settings, 'foobar', queue, raise_error=False)

        fake_realtime.get_connection.assert_called_once_with(settings)

    def test_passes_connection_to_consumer(self, fake_realtime, fake_consumer, queue):
        messages.process_messages({}, 'foobar', queue, raise_error=False)

        fake_consumer.assert_called_once_with(connection=fake_realtime.get_connection.return_value,
                                              routing_key=mock.ANY,
                                              handler=mock.ANY,
                                              sentry_client=mock.ANY)

    def test_runs_consumer(self, fake_consumer, queue):
        messages.process_messages({}, 'foobar', queue, raise_error=False)

        consumer = fake_consumer.return_value
        consumer.run.assert_called_once_with()

    def test_message_handler_puts_message_on_queue(self, fake_consumer, queue):
        messages.process_messages({}, 'foobar', queue, raise_error=False)
        message_handler = fake_consumer.call_args[1]['handler']
        message_handler({'foo': 'bar'})
        result = queue.get_nowait()

        assert result.topic == 'foobar'
        assert result.payload == {'foo': 'bar'}

    @pytest.fixture
    def fake_sentry(self, patch):
        return patch('h.sentry')

    @pytest.fixture
    def fake_consumer(self, patch):
        return patch('h.streamer.messages.Consumer')

    @pytest.fixture
    def fake_realtime(self, patch):
        return patch('h.streamer.messages.realtime')

    @pytest.fixture
    def queue(self):
        return Queue()


class TestHandleMessage(object):
    def test_calls_handler_once_per_socket_with_deserialized_message(self, websocket):
        handler = mock.Mock(return_value=None)
        message = messages.Message(topic='foo', payload={'foo': 'bar'})
        websocket.instances = [FakeSocket('a'), FakeSocket('b')]

        messages.handle_message(message, topic_handlers={'foo': handler})

        print(repr(mock.call({'foo': 'bar'}, websocket.instances[0])))
        print(repr(handler.mock_calls[0]))
        assert handler.mock_calls == [
            mock.call({'foo': 'bar'}, websocket.instances[0]),
            mock.call({'foo': 'bar'}, websocket.instances[1]),
        ]

    def test_sends_serialized_messages_down_websocket(self, websocket):
        handler = mock.Mock(return_value={'just': 'some message'})
        message = messages.Message(topic='foo', payload={'foo': 'bar'})
        socket = FakeSocket('a')
        websocket.instances = [socket]

        messages.handle_message(message, topic_handlers={'foo': handler})

        socket.send.assert_called_once_with('{"just": "some message"}')

    def test_does_not_send_messages_down_websocket_if_handler_response_is_none(self, websocket):
        handler = mock.Mock(return_value=None)
        message = messages.Message(topic='foo', payload={'foo': 'bar'})
        socket = FakeSocket('a')
        websocket.instances = [socket]

        messages.handle_message(message, topic_handlers={'foo': handler})

        assert socket.send.call_count == 0

    def test_does_not_send_messages_down_websocket_if_socket_terminated(self, websocket):
        handler = mock.Mock(return_value={'just': 'some message'})
        message = messages.Message(topic='foo', payload={'foo': 'bar'})
        socket = FakeSocket('a')
        socket.terminated = True
        websocket.instances = [socket]

        messages.handle_message(message, topic_handlers={'foo': handler})

        assert socket.send.call_count == 0

    @pytest.fixture
    def websocket(self, patch):
        return patch('h.streamer.websocket.WebSocket')


class TestHandleAnnotationEvent(object):
    def test_notification_format(self):
        """Check the format of the returned notification in the happy case."""
        message = {
            'annotation': {'permissions': {'read': ['group:__world__']}},
            'action': 'update',
            'src_client_id': 'pigeon'
        }
        socket = FakeSocket('giraffe')

        assert messages.handle_annotation_event(message, socket) == {
            'payload': [message['annotation']],
            'type': 'annotation-notification',
            'options': {'action': 'update'},
        }

    def test_none_for_sender_socket(self):
        """Should return None if the socket's client_id matches the message's."""
        message = {
            'annotation': {'permissions': {'read': ['group:__world__']}},
            'action': 'update',
            'src_client_id': 'pigeon'
        }
        socket = FakeSocket('pigeon')

        assert messages.handle_annotation_event(message, socket) is None

    def test_none_if_no_socket_filter(self):
        """Should return None if the socket has no filter."""
        message = {
            'annotation': {'permissions': {'read': ['group:__world__']}},
            'action': 'update',
            'src_client_id': 'pigeon'
        }
        socket = FakeSocket('giraffe')
        socket.filter = None

        assert messages.handle_annotation_event(message, socket) is None

    def test_none_if_action_is_read(self):
        """Should return None if the message action is 'read'."""
        message = {
            'annotation': {'permissions': {'read': ['group:__world__']}},
            'action': 'read',
            'src_client_id': 'pigeon'
        }
        socket = FakeSocket('giraffe')

        assert messages.handle_annotation_event(message, socket) is None

    def test_none_if_filter_does_not_match(self):
        """Should return None if the socket filter doesn't match the message."""
        message = {
            'annotation': {'permissions': {'read': ['group:__world__']}},
            'action': 'update',
            'src_client_id': 'pigeon'
        }
        socket = FakeSocket('giraffe')
        socket.filter.match.return_value = False

        assert messages.handle_annotation_event(message, socket) is None

    def test_none_if_annotation_nipsad(self):
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

        assert messages.handle_annotation_event(message, socket) is None

    def test_sends_nipsad_annotations_to_owners(self):
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

        assert messages.handle_annotation_event(message, socket) is not None

    def test_sends_if_annotation_public(self):
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

        assert messages.handle_annotation_event(message, socket) is not None

    def test_none_if_not_in_group(self):
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

        assert messages.handle_annotation_event(message, socket) is None

    def test_sends_if_in_group(self):
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

        assert messages.handle_annotation_event(message, socket) is not None


class TestHandleUserEvent(object):
    def test_sends_session_change_when_joining_or_leaving_group(self):
        session_model = mock.Mock()
        message = {
            'type': 'group-join',
            'userid': 'amy',
            'group': 'groupid',
            'session_model': session_model,
        }

        sock = FakeSocket('clientid')
        sock.request.authenticated_userid = 'amy'

        assert messages.handle_user_event(message, sock) == {
            'type': 'session-change',
            'action': 'group-join',
            'model': session_model,
        }

    def test_none_when_socket_is_not_event_users(self):
        """Don't send session-change events if the event user is not the socket user."""
        message = {
            'type': 'group-join',
            'userid': 'amy',
            'group': 'groupid',
        }

        sock = FakeSocket('clientid')
        sock.request.authenticated_userid = 'bob'

        assert messages.handle_user_event(message, sock) is None
