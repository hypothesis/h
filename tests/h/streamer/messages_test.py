# -*- coding: utf-8 -*-

import mock
import pytest
from gevent.queue import Queue
from pyramid import security
from pyramid import registry

from h.streamer import messages


class FakeSocket(object):
    client_id = None
    filter = None
    terminated = None

    def __init__(self, client_id):
        self.client_id = client_id
        self.terminated = False
        self.filter = mock.MagicMock()
        self.send = mock.MagicMock()

        self.authenticated_userid = None
        self.effective_principals = [security.Everyone, 'group:__world__']
        self.registry = registry.Registry('streamer_test')
        self.registry.settings = {'h.app_url': 'http://streamer'}

        self.send_json_payloads = []

    def send_json(self, payload):
        self.send_json_payloads.append(payload)


@pytest.mark.usefixtures('fake_sentry', 'fake_stats')
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
                                              sentry_client=fake_sentry.get_client.return_value,
                                              statsd_client=mock.ANY)

    def test_creates_statsd_client(self, fake_stats, fake_consumer, queue):
        settings = {}

        messages.process_messages(settings, 'foobar', queue, raise_error=False)

        fake_stats.get_client.assert_called_once_with(settings)

    def test_passes_stats_client_to_consumer(self, fake_stats, fake_consumer, queue):
        messages.process_messages({}, 'foobar', queue, raise_error=False)

        fake_consumer.assert_called_once_with(connection=mock.ANY,
                                              routing_key=mock.ANY,
                                              handler=mock.ANY,
                                              sentry_client=mock.ANY,
                                              statsd_client=fake_stats.get_client.return_value)

    def test_passes_routing_key_to_consumer(self, fake_consumer, queue):
        messages.process_messages({}, 'foobar', queue, raise_error=False)

        fake_consumer.assert_called_once_with(connection=mock.ANY,
                                              routing_key='foobar',
                                              handler=mock.ANY,
                                              sentry_client=mock.ANY,
                                              statsd_client=mock.ANY)

    def test_initializes_new_connection(self, fake_realtime, fake_consumer, queue):
        settings = {}
        messages.process_messages(settings, 'foobar', queue, raise_error=False)

        fake_realtime.get_connection.assert_called_once_with(settings)

    def test_passes_connection_to_consumer(self, fake_realtime, fake_consumer, queue):
        messages.process_messages({}, 'foobar', queue, raise_error=False)

        fake_consumer.assert_called_once_with(connection=fake_realtime.get_connection.return_value,
                                              routing_key=mock.ANY,
                                              handler=mock.ANY,
                                              sentry_client=mock.ANY,
                                              statsd_client=mock.ANY)

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
    def fake_stats(self, patch):
        return patch('h.stats')

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
    def test_calls_handler_with_list_of_sockets(self, websocket):
        handler = mock.Mock(return_value=None)
        session = mock.sentinel.db_session
        message = messages.Message(topic='foo', payload={'foo': 'bar'})
        websocket.instances = [FakeSocket('a'), FakeSocket('b')]

        messages.handle_message(message, session, topic_handlers={'foo': handler})

        handler.assert_called_once_with(message.payload, list(websocket.instances), session)

    @pytest.fixture
    def websocket(self, patch):
        return patch('h.streamer.websocket.WebSocket')


@pytest.mark.usefixtures('fetch_annotation', 'links_service', 'nipsa_service')
class TestHandleAnnotationEvent(object):
    def test_it_fetches_the_annotation(self, fetch_annotation, presenter_asdict):
        message = {
            'annotation_id': 'panda',
            'action': 'update',
            'src_client_id': 'pigeon'
        }
        socket = FakeSocket('giraffe')
        session = mock.sentinel.db_session
        presenter_asdict.return_value = self.serialized_annotation()

        messages.handle_annotation_event(message, [socket], session)

        fetch_annotation.assert_called_once_with(session, 'panda')

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
        session = mock.sentinel.db_session
        fetch_annotation.return_value = None

        result = messages.handle_annotation_event(message, [socket], session)

        assert result is None

    def test_it_serializes_the_annotation(self,
                                          fetch_annotation,
                                          links_service,
                                          presenters):
        message = {'action': '_', 'annotation_id': '_', 'src_client_id': '_'}
        socket = FakeSocket('giraffe')
        session = mock.sentinel.db_session
        presenters.AnnotationJSONPresenter.return_value.asdict.return_value = (
            self.serialized_annotation())

        messages.handle_annotation_event(message, [socket], session)

        presenters.AnnotationJSONPresenter.assert_called_once_with(
            fetch_annotation.return_value,
            links_service.return_value)
        assert presenters.AnnotationJSONPresenter.return_value.asdict.called

    def test_notification_format(self, presenter_asdict):
        """Check the format of the returned notification in the happy case."""
        message = {
            'annotation_id': 'panda',
            'action': 'update',
            'src_client_id': 'pigeon'
        }
        socket = FakeSocket('giraffe')
        session = mock.sentinel.db_session
        presenter_asdict.return_value = self.serialized_annotation()

        messages.handle_annotation_event(message, [socket], session)

        assert socket.send_json_payloads[0] == {
            'payload': [self.serialized_annotation()],
            'type': 'annotation-notification',
            'options': {'action': 'update'},
        }

    def test_no_send_for_sender_socket(self, presenter_asdict):
        """Should return None if the socket's client_id matches the message's."""
        message = {'src_client_id': 'pigeon', 'annotation_id': '_', 'action': '_'}
        socket = FakeSocket('pigeon')
        session = mock.sentinel.db_session
        presenter_asdict.return_value = self.serialized_annotation()

        messages.handle_annotation_event(message, [socket], session)

        assert socket.send_json_payloads == []

    def test_no_send_if_no_socket_filter(self, presenter_asdict):
        """Should return None if the socket has no filter."""
        message = {'src_client_id': '_', 'annotation_id': '_', 'action': '_'}
        socket = FakeSocket('giraffe')
        socket.filter = None
        session = mock.sentinel.db_session
        presenter_asdict.return_value = self.serialized_annotation()

        messages.handle_annotation_event(message, [socket], session)

        assert socket.send_json_payloads == []

    def test_no_send_if_action_is_read(self, presenter_asdict):
        """Should return None if the message action is 'read'."""
        message = {'action': 'read', 'src_client_id': '_', 'annotation_id': '_'}
        socket = FakeSocket('giraffe')
        session = mock.sentinel.db_session
        presenter_asdict.return_value = self.serialized_annotation()

        messages.handle_annotation_event(message, [socket], session)

        assert socket.send_json_payloads == []

    def test_no_send_if_filter_does_not_match(self, presenter_asdict):
        """Should return None if the socket filter doesn't match the message."""
        message = {'action': '_', 'src_client_id': '_', 'annotation_id': '_'}
        socket = FakeSocket('giraffe')
        socket.filter.match.return_value = False
        session = mock.sentinel.db_session
        presenter_asdict.return_value = self.serialized_annotation()

        messages.handle_annotation_event(message, [socket], session)

        assert socket.send_json_payloads == []

    def test_no_send_if_annotation_nipsad(self, nipsa_service, presenter_asdict):
        """Should return None if the annotation is from a NIPSA'd user."""
        message = {'action': '_', 'src_client_id': '_', 'annotation_id': '_'}
        socket = FakeSocket('giraffe')
        session = mock.sentinel.db_session
        presenter_asdict.return_value = self.serialized_annotation()
        nipsa_service.return_value.is_flagged.return_value = True

        messages.handle_annotation_event(message, [socket], session)

        assert socket.send_json_payloads == []

    def test_no_send_if_annotation_delete_nipsad(self, fetch_annotation, nipsa_service):
        """
        Should return None if the annotation is a deletion from a NIPSA'd
        user.
        """
        message = {
            'action': 'delete',
            'src_client_id': '_',
            'annotation_id': '_',
            'annotation_dict': self.serialized_annotation({'user': 'geraldine'}),
        }
        fetch_annotation.return_value = None
        socket = FakeSocket('giraffe')
        session = mock.sentinel.db_session
        def is_flagged(userid):
            return userid == 'geraldine'
        nipsa_service.return_value.is_flagged.side_effect = is_flagged

        messages.handle_annotation_event(message, [socket], session)

        assert socket.send_json_payloads == []

    def test_sends_nipsad_annotations_to_owners(self, nipsa_service, presenter_asdict):
        """NIPSA'd users should see their own annotations."""
        message = {'action': '_', 'src_client_id': '_', 'annotation_id': '_'}
        socket = FakeSocket('giraffe')
        socket.authenticated_userid = 'fred'
        session = mock.sentinel.db_session
        presenter_asdict.return_value = self.serialized_annotation()
        nipsa_service.return_value.is_flagged.return_value = True

        messages.handle_annotation_event(message, [socket], session)

        assert len(socket.send_json_payloads) == 1

    def test_sends_nipsad_deletes_to_owners(self, fetch_annotation, nipsa_service):
        """NIPSA'd users should see their own deletions."""
        message = {
            'action': 'delete',
            'src_client_id': '_',
            'annotation_id': '_',
            'annotation_dict': self.serialized_annotation({'user': 'geraldine'}),
        }
        fetch_annotation.return_value = None
        socket = FakeSocket('giraffe')
        socket.authenticated_userid = 'geraldine'
        session = mock.sentinel.db_session
        def is_flagged(userid):
            return userid == 'geraldine'
        nipsa_service.return_value.is_flagged.side_effect = is_flagged

        messages.handle_annotation_event(message, [socket], session)

        assert len(socket.send_json_payloads) == 1

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
        session = mock.sentinel.db_session
        presenter_asdict.return_value = self.serialized_annotation()

        messages.handle_annotation_event(message, [socket], session)

        assert len(socket.send_json_payloads) == 1

    def test_no_send_if_not_in_group(self, presenter_asdict):
        """Users shouldn't see annotations in groups they aren't members of."""
        message = {'action': '_', 'src_client_id': '_', 'annotation_id': '_'}
        socket = FakeSocket('giraffe')
        socket.authenticated_userid = 'fred'
        session = mock.sentinel.db_session
        presenter_asdict.return_value = self.serialized_annotation({
            'permissions': {'read': ['group:private-group']}})

        messages.handle_annotation_event(message, [socket], session)

        assert socket.send_json_payloads == []

    def test_sends_if_in_group(self, presenter_asdict):
        """Users should see annotations in groups they are members of."""
        message = {'action': '_', 'src_client_id': '_', 'annotation_id': '_'}
        socket = FakeSocket('giraffe')
        socket.authenticated_userid = 'fred'
        socket.effective_principals.append('group:private-group')
        session = mock.sentinel.db_session
        presenter_asdict.return_value = self.serialized_annotation({
            'permissions': {'read': ['group:private-group']}})

        messages.handle_annotation_event(message, [socket], session)

        assert len(socket.send_json_payloads) == 1

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
    def links_service(self, patch):
        return patch('h.streamer.messages.LinksService')

    @pytest.fixture
    def nipsa_service(self, patch):
        service = patch('h.streamer.messages.NipsaService')
        service.return_value.is_flagged.return_value = False
        return service


class TestHandleUserEvent(object):
    def test_sends_session_change_when_joining_or_leaving_group(self):
        session_model = mock.Mock()
        message = {
            'type': 'group-join',
            'userid': 'amy',
            'group': 'groupid',
            'session_model': session_model,
        }
        socket = FakeSocket('clientid')
        socket.authenticated_userid = 'amy'

        messages.handle_user_event(message, [socket], None)

        assert socket.send_json_payloads[0] == {
            'type': 'session-change',
            'action': 'group-join',
            'model': session_model,
        }

    def test_no_send_when_socket_is_not_event_users(self):
        """Don't send session-change events if the event user is not the socket user."""
        message = {
            'type': 'group-join',
            'userid': 'amy',
            'group': 'groupid',
        }
        socket = FakeSocket('clientid')
        socket.authenticated_userid = 'bob'

        messages.handle_user_event(message, [socket], None)

        assert socket.send_json_payloads == []
