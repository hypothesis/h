from gevent.queue import Queue
import mock
from pyramid.request import apply_request_extensions
from pyramid.testing import DummyRequest
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
        self.request = DummyRequest(db=mock.sentinel.db_session)
        self.send = mock.MagicMock()
        apply_request_extensions(self.request)


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


@pytest.mark.usefixtures('fetch_annotation', 'nipsa_service')
class TestHandleAnnotationEvent(object):
    def test_it_fetches_the_annotation(self, fetch_annotation, presenter_asdict):
        message = {
            'annotation_id': 'panda',
            'action': 'update',
            'src_client_id': 'pigeon'
        }
        socket = FakeSocket('giraffe')
        presenter_asdict.return_value = self.serialized_annotation()

        messages.handle_annotation_event(message, socket)

        fetch_annotation.assert_called_once_with(socket.request.db, 'panda')

    def test_it_skips_notification_when_fetch_failed(self, fetch_annotation):
        """
        When a create/update and a delete event happens in quick succession
        we could fail to load the annotation, even though the event action is
        update/create. This tests that in that case we silently abort and don't
        sent a notification to the client.
        """
        message = {
            'annotation_id': 'panda',
            'action': 'update',
            'src_client_id': 'pigeon'
        }
        socket = FakeSocket('giraffe')
        fetch_annotation.return_value = None

        assert messages.handle_annotation_event(message, socket) is None

    def test_it_serializes_the_annotation(self,
                                          fetch_annotation,
                                          presenters):
        message = {'action': '_', 'annotation_id': '_', 'src_client_id': '_'}
        socket = FakeSocket('giraffe')
        presenters.AnnotationJSONPresenter.return_value.asdict.return_value = (
            self.serialized_annotation())

        messages.handle_annotation_event(message, socket)

        presenters.AnnotationJSONPresenter.assert_called_once_with(
            socket.request, fetch_annotation.return_value)
        assert presenters.AnnotationJSONPresenter.return_value.asdict.called

    def test_notification_format(self, presenter_asdict):
        """Check the format of the returned notification in the happy case."""
        message = {
            'annotation_id': 'panda',
            'action': 'update',
            'src_client_id': 'pigeon'
        }
        socket = FakeSocket('giraffe')
        presenter_asdict.return_value = self.serialized_annotation()

        assert messages.handle_annotation_event(message, socket) == {
            'payload': [self.serialized_annotation()],
            'type': 'annotation-notification',
            'options': {'action': 'update'},
        }

    def test_none_for_sender_socket(self, presenter_asdict):
        """Should return None if the socket's client_id matches the message's."""
        message = {'src_client_id': 'pigeon', 'annotation_id': '_', 'action': '_'}
        socket = FakeSocket('pigeon')
        presenter_asdict.return_value = self.serialized_annotation()

        result = messages.handle_annotation_event(message, socket)
        assert result is None

    def test_none_if_no_socket_filter(self, presenter_asdict):
        """Should return None if the socket has no filter."""
        message = {'src_client_id': '_', 'annotation_id': '_', 'action': '_'}
        socket = FakeSocket('giraffe')
        socket.filter = None
        presenter_asdict.return_value = self.serialized_annotation()

        result = messages.handle_annotation_event(message, socket)
        assert result is None

    def test_none_if_action_is_read(self, presenter_asdict):
        """Should return None if the message action is 'read'."""
        message = {'action': 'read', 'src_client_id': '_', 'annotation_id': '_'}
        socket = FakeSocket('giraffe')
        presenter_asdict.return_value = self.serialized_annotation()

        result = messages.handle_annotation_event(message, socket)
        assert result is None

    def test_none_if_filter_does_not_match(self, presenter_asdict):
        """Should return None if the socket filter doesn't match the message."""
        message = {'action': '_', 'src_client_id': '_', 'annotation_id': '_'}
        socket = FakeSocket('giraffe')
        socket.filter.match.return_value = False
        presenter_asdict.return_value = self.serialized_annotation()

        result = messages.handle_annotation_event(message, socket)
        assert result is None

    def test_none_if_annotation_nipsad(self, nipsa_service, presenter_asdict):
        """Should return None if the annotation is from a NIPSA'd user."""
        message = {'action': '_', 'src_client_id': '_', 'annotation_id': '_'}
        socket = FakeSocket('giraffe')
        presenter_asdict.return_value = self.serialized_annotation()
        nipsa_service.is_flagged.return_value = True

        result = messages.handle_annotation_event(message, socket)
        assert result is None

    def test_sends_nipsad_annotations_to_owners(self, config, presenter_asdict):
        """NIPSA'd users should see their own annotations."""
        config.testing_securitypolicy('fred')
        message = {'action': '_', 'src_client_id': '_', 'annotation_id': '_'}
        socket = FakeSocket('giraffe')
        presenter_asdict.return_value = self.serialized_annotation({'nipsa': True})

        result = messages.handle_annotation_event(message, socket)
        assert result is not None

    def test_sends_if_annotation_public(self, presenter_asdict):
        """
        Everyone should see annotations which are public.

        When logged-out, effective principals contains only
        `pyramid.security.Everyone`. This test ensures that the system
        principal is correctly equated with the annotation principal
        'group:__world__', ensuring that everyone (including logged-out users)
        receives all public annotations.
        """
        message = {'action': '_', 'src_client_id': '_', 'annotation_id': '_'}
        socket = FakeSocket('giraffe')
        presenter_asdict.return_value = self.serialized_annotation()

        result = messages.handle_annotation_event(message, socket)
        assert result is not None

    def test_none_if_not_in_group(self, config, presenter_asdict):
        """Users shouldn't see annotations in groups they aren't members of."""
        config.testing_securitypolicy('fred')
        message = {'action': '_', 'src_client_id': '_', 'annotation_id': '_'}
        socket = FakeSocket('giraffe')
        presenter_asdict.return_value = self.serialized_annotation({
            'permissions': {'read': ['group:private-group']}})

        result = messages.handle_annotation_event(message, socket)
        assert result is None

    def test_sends_if_in_group(self, config, presenter_asdict):
        """Users should see annotations in groups they are members of."""
        config.testing_securitypolicy('fred', groupids=['group:private-group'])
        message = {'action': '_', 'src_client_id': '_', 'annotation_id': '_'}
        socket = FakeSocket('giraffe')
        presenter_asdict.return_value = self.serialized_annotation({
            'permissions': {'read': ['group:private-group']}})

        result = messages.handle_annotation_event(message, socket)
        assert result is not None

    def serialized_annotation(self, data=None):
        if data is None:
            data = {}

        serialized = {
            'user': 'fred',
            'permissions': {'read': ['group:__world__']}
        }
        serialized.update(data)

        return serialized

    @pytest.fixture
    def fetch_annotation(self, patch):
        return patch('h.streamer.messages.storage.fetch_annotation')

    @pytest.fixture
    def presenters(self, patch):
        return patch('h.streamer.messages.presenters')

    @pytest.fixture
    def presenter_asdict(self, patch):
        return patch('h.streamer.messages.presenters.AnnotationJSONPresenter.asdict')

    @pytest.fixture
    def nipsa_service(self, config):
        service = mock.Mock(spec_set=['is_flagged'])
        service.is_flagged.return_value = False

        config.include('pyramid_services')
        config.register_service(service, name='nipsa')

        return service

class TestHandleUserEvent(object):
    def test_sends_session_change_when_joining_or_leaving_group(self, config):
        config.testing_securitypolicy('amy')
        session_model = mock.Mock()
        message = {
            'type': 'group-join',
            'userid': 'amy',
            'group': 'groupid',
            'session_model': session_model,
        }

        sock = FakeSocket('clientid')

        assert messages.handle_user_event(message, sock) == {
            'type': 'session-change',
            'action': 'group-join',
            'model': session_model,
        }

    def test_none_when_socket_is_not_event_users(self, config):
        """Don't send session-change events if the event user is not the socket user."""
        config.testing_securitypolicy('bob')
        message = {
            'type': 'group-join',
            'userid': 'amy',
            'group': 'groupid',
        }

        sock = FakeSocket('clientid')

        assert messages.handle_user_event(message, sock) is None
