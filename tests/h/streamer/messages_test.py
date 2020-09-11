from unittest import mock

import pytest
from gevent.queue import Queue
from h_matchers import Any
from pyramid import registry, security

from h.streamer import messages


class FakeSocket:
    client_id = None
    terminated = None

    def __init__(self, client_id):
        self.client_id = client_id
        self.terminated = False
        self.send = mock.MagicMock()

        self.authenticated_userid = None
        self.effective_principals = [security.Everyone, "group:__world__"]
        self.registry = registry.Registry("streamer_test")
        self.registry.settings = {"h.app_url": "http://streamer"}

        self.send_json_payloads = []

    def send_json(self, payload):
        self.send_json_payloads.append(payload)


class TestProcessMessages:
    def test_passes_routing_key_to_consumer(self, fake_consumer, queue):
        messages.process_messages({}, "foobar", queue, raise_error=False)

        fake_consumer.assert_called_once_with(
            connection=Any(), routing_key="foobar", handler=Any()
        )

    def test_initializes_new_connection(self, fake_realtime, fake_consumer, queue):
        settings = {}
        messages.process_messages(settings, "foobar", queue, raise_error=False)

        fake_realtime.get_connection.assert_called_once_with(settings)

    def test_passes_connection_to_consumer(self, fake_realtime, fake_consumer, queue):
        messages.process_messages({}, "foobar", queue, raise_error=False)

        fake_consumer.assert_called_once_with(
            connection=fake_realtime.get_connection.return_value,
            routing_key=Any(),
            handler=Any(),
        )

    def test_runs_consumer(self, fake_consumer, queue):
        messages.process_messages({}, "foobar", queue, raise_error=False)

        consumer = fake_consumer.return_value
        consumer.run.assert_called_once_with()

    def test_message_handler_puts_message_on_queue(self, fake_consumer, queue):
        messages.process_messages({}, "foobar", queue, raise_error=False)
        message_handler = fake_consumer.call_args[1]["handler"]
        message_handler({"foo": "bar"})
        result = queue.get_nowait()

        assert result.topic == "foobar"
        assert result.payload == {"foo": "bar"}

    @pytest.fixture
    def fake_consumer(self, patch):
        return patch("h.streamer.messages.Consumer")

    @pytest.fixture
    def fake_realtime(self, patch):
        return patch("h.streamer.messages.realtime")

    @pytest.fixture
    def queue(self):
        return Queue()


class TestHandleMessage:
    def test_calls_handler_with_list_of_sockets(self, websocket):
        handler = mock.Mock(return_value=None)
        session = mock.sentinel.db_session
        settings = mock.sentinel.settings
        message = messages.Message(topic="foo", payload={"foo": "bar"})
        websocket.instances = [FakeSocket("a"), FakeSocket("b")]

        messages.handle_message(
            message, settings, session, topic_handlers={"foo": handler}
        )

        handler.assert_called_once_with(
            message.payload, list(websocket.instances), settings, session
        )

    @pytest.fixture
    def websocket(self, patch):
        return patch("h.streamer.websocket.WebSocket")


@pytest.mark.usefixtures(
    "fetch_annotation",
    "user_service",
    "groupfinder_service",
    "links_service",
    "nipsa_service",
)
class TestHandleAnnotationEvent:
    def test_it_fetches_the_annotation(self, fetch_annotation, presenter_asdict):
        message = {
            "annotation_id": "panda",
            "action": "update",
            "src_client_id": "pigeon",
        }
        socket = FakeSocket("giraffe")
        session = mock.sentinel.db_session
        settings = {"foo": "bar"}
        presenter_asdict.return_value = self.serialized_annotation()

        messages.handle_annotation_event(message, [socket], settings, session)

        fetch_annotation.assert_called_once_with(session, "panda")

    def test_it_skips_notification_when_fetch_failed(self, fetch_annotation):
        """
        When a create/update and a delete event happens in quick succession
        we could fail to load the annotation, even though the event action is
        update/create. This tests that in that case we silently abort and don't
        sent a notification to the client.
        """
        message = {
            "annotation_id": "panda",
            "action": "update",
            "src_client_id": "pigeon",
        }
        socket = FakeSocket("giraffe")
        session = mock.sentinel.db_session
        settings = {"foo": "bar"}
        fetch_annotation.return_value = None

        result = messages.handle_annotation_event(message, [socket], settings, session)

        assert result is None

    def test_it_initializes_groupfinder_service(self, groupfinder_service):
        message = {"action": "_", "annotation_id": "_", "src_client_id": "_"}
        session = mock.sentinel.db_session
        socket = FakeSocket("giraffe")
        settings = {"h.authority": "example.org"}

        messages.handle_annotation_event(message, [socket], settings, session)

        groupfinder_service.assert_called_once_with(session, "example.org")

    def test_it_serializes_the_annotation(
        self,
        fetch_annotation,
        links_service,
        groupfinder_service,
        annotation_resource,
        presenters,
        AnnotationUserInfoFormatter,
    ):
        message = {"action": "_", "annotation_id": "_", "src_client_id": "_"}
        socket = FakeSocket("giraffe")
        session = mock.sentinel.db_session
        settings = {"foo": "bar"}
        presenters.AnnotationJSONPresenter.return_value.asdict.return_value = (
            self.serialized_annotation()
        )

        messages.handle_annotation_event(message, [socket], settings, session)

        annotation_resource.assert_called_once_with(
            fetch_annotation.return_value,
            groupfinder_service.return_value,
            links_service.return_value,
        )

        presenters.AnnotationJSONPresenter.assert_called_once_with(
            annotation_resource.return_value,
            formatters=[AnnotationUserInfoFormatter.return_value],
        )
        assert presenters.AnnotationJSONPresenter.return_value.asdict.called

    def test_notification_format(self, presenter_asdict):
        """Check the format of the returned notification in the happy case."""
        message = {
            "annotation_id": "panda",
            "action": "update",
            "src_client_id": "pigeon",
        }
        socket = FakeSocket("giraffe")
        session = mock.sentinel.db_session
        settings = {"foo": "bar"}
        presenter_asdict.return_value = self.serialized_annotation()

        messages.handle_annotation_event(message, [socket], settings, session)

        assert socket.send_json_payloads[0] == {
            "payload": [self.serialized_annotation()],
            "type": "annotation-notification",
            "options": {"action": "update"},
        }

    def test_notification_format_delete(
        self, fetch_annotation, presenter_asdict, principals_allowed_by_permission
    ):
        """Check the format of the returned notification for deletes."""
        message = {"annotation_id": "_", "action": "delete", "src_client_id": "pigeon"}
        annotation = fetch_annotation.return_value
        socket = FakeSocket("giraffe")
        session = mock.sentinel.db_session
        settings = {"foo": "bar"}
        principals_allowed_by_permission.return_value = socket.effective_principals

        messages.handle_annotation_event(message, [socket], settings, session)

        presenter_asdict.assert_not_called()
        assert socket.send_json_payloads[0] == {
            "payload": [{"id": annotation.id}],
            "type": "annotation-notification",
            "options": {"action": "delete"},
        }

    def test_no_send_for_sender_socket(self, presenter_asdict):
        """Should return None if the socket's client_id matches the message's."""
        message = {"src_client_id": "pigeon", "annotation_id": "_", "action": "_"}
        socket = FakeSocket("pigeon")
        session = mock.sentinel.db_session
        settings = {"foo": "bar"}
        presenter_asdict.return_value = self.serialized_annotation()

        messages.handle_annotation_event(message, [socket], settings, session)

        assert socket.send_json_payloads == []

    @pytest.mark.usefixtures("no_matching_sockets")
    def test_no_send_if_no_socket_filter(self, presenter_asdict):
        """Should return None if the socket has no filter."""
        message = {"src_client_id": "_", "annotation_id": "_", "action": "_"}
        socket = FakeSocket("giraffe")
        session = mock.sentinel.db_session
        settings = {"foo": "bar"}
        presenter_asdict.return_value = self.serialized_annotation()

        messages.handle_annotation_event(message, [socket], settings, session)

        assert socket.send_json_payloads == []

    def test_no_send_if_action_is_read(self, presenter_asdict):
        """Should return None if the message action is 'read'."""
        message = {"action": "read", "src_client_id": "_", "annotation_id": "_"}
        socket = FakeSocket("giraffe")
        session = mock.sentinel.db_session
        settings = {"foo": "bar"}
        presenter_asdict.return_value = self.serialized_annotation()

        messages.handle_annotation_event(message, [socket], settings, session)

        assert socket.send_json_payloads == []

    @pytest.mark.usefixtures("no_matching_sockets")
    def test_no_send_if_filter_does_not_match(self, presenter_asdict):
        """Should return None if the socket filter doesn't match the message."""
        message = {"action": "_", "src_client_id": "_", "annotation_id": "_"}
        socket = FakeSocket("giraffe")

        session = mock.sentinel.db_session
        settings = {"foo": "bar"}
        presenter_asdict.return_value = self.serialized_annotation()

        messages.handle_annotation_event(message, [socket], settings, session)

        assert socket.send_json_payloads == []

    def test_no_send_if_annotation_nipsad(self, nipsa_service, presenter_asdict):
        """Should return None if the annotation is from a NIPSA'd user."""
        message = {"action": "_", "src_client_id": "_", "annotation_id": "_"}
        socket = FakeSocket("giraffe")
        session = mock.sentinel.db_session
        settings = {"foo": "bar"}
        presenter_asdict.return_value = self.serialized_annotation()
        nipsa_service.return_value.is_flagged.return_value = True

        messages.handle_annotation_event(message, [socket], settings, session)

        assert socket.send_json_payloads == []

    def test_sends_nipsad_annotations_to_owners(
        self, fetch_annotation, nipsa_service, presenter_asdict
    ):
        """NIPSA'd users should see their own annotations."""
        message = {"action": "_", "src_client_id": "_", "annotation_id": "_"}
        fetch_annotation.return_value.userid = "fred"
        socket = FakeSocket("giraffe")
        socket.authenticated_userid = "fred"
        session = mock.sentinel.db_session
        settings = {"foo": "bar"}
        presenter_asdict.return_value = self.serialized_annotation()
        nipsa_service.return_value.is_flagged.return_value = True

        messages.handle_annotation_event(message, [socket], settings, session)

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
        message = {"action": "_", "src_client_id": "_", "annotation_id": "_"}
        socket = FakeSocket("giraffe")
        session = mock.sentinel.db_session
        settings = {"foo": "bar"}
        presenter_asdict.return_value = self.serialized_annotation()

        messages.handle_annotation_event(message, [socket], settings, session)

        assert len(socket.send_json_payloads) == 1

    def test_no_send_if_not_in_group(
        self, annotation_resource, presenters, principals_allowed_by_permission
    ):
        """Users shouldn't see annotations in groups they aren't members of."""
        message = {"action": "_", "src_client_id": "_", "annotation_id": "_"}
        socket = FakeSocket("giraffe")
        socket.authenticated_userid = "fred"
        session = mock.sentinel.db_session
        settings = {"foo": "bar"}
        principals_allowed_by_permission.return_value = ["group:private-group"]

        messages.handle_annotation_event(message, [socket], settings, session)

        principals_allowed_by_permission.assert_called_with(
            annotation_resource.return_value, "read"
        )
        assert socket.send_json_payloads == []

    def test_sends_if_in_group(
        self, annotation_resource, presenters, principals_allowed_by_permission
    ):
        """Users should see annotations in groups they are members of."""
        message = {"action": "_", "src_client_id": "_", "annotation_id": "_"}
        socket = FakeSocket("giraffe")
        socket.authenticated_userid = "fred"
        session = mock.sentinel.db_session
        settings = {"foo": "bar"}

        principals_allowed_by_permission.return_value = ["group:private-group"]
        socket.effective_principals.append("group:private-group")

        messages.handle_annotation_event(message, [socket], settings, session)

        principals_allowed_by_permission.assert_called_with(
            annotation_resource.return_value, "read"
        )
        assert len(socket.send_json_payloads) == 1

    @pytest.mark.parametrize(
        "is_shared,socket_principals,expect_send",
        [
            # Only members of a private group get notified when shared annotations
            # in that group are deleted.
            (True, ["user:bob", "group:foobar"], True),
            (True, ["group:foobar"], True),
            (True, [security.Everyone], False),
            # Only creators of private annotations get notified when they are
            # deleted.
            (False, ["user:bob", "group:foobar"], True),
            (False, ["group:foobar"], False),
            (False, [security.Everyone], False),
        ],
    )
    def test_sends_annotation_delete_if_permissions_correct(
        self,
        fetch_annotation,
        annotation_resource,
        principals_allowed_by_permission,
        is_shared,
        socket_principals,
        expect_send,
    ):
        message = {"annotation_id": "_", "action": "delete", "src_client_id": "pigeon"}
        annotation = fetch_annotation.return_value
        annotation.userid = "user:bob"
        socket = FakeSocket("giraffe")
        session = mock.sentinel.db_session
        settings = {"foo": "bar"}

        def principals(resource, permission):
            if (
                resource == annotation_resource.return_value.group
                and permission == "read"
            ):
                return ["group:foobar"]
            else:
                return []

        principals_allowed_by_permission.side_effect = principals

        annotation.shared = is_shared
        socket.effective_principals = socket_principals

        messages.handle_annotation_event(message, [socket], settings, session)

        assert bool(socket.send_json_payloads) == expect_send

    def serialized_annotation(self):
        return {"permissions": {"read": ["group:__world__"]}}

    @pytest.fixture
    def fetch_annotation(self, factories, patch):
        fetch = patch("h.streamer.messages.storage.fetch_annotation")
        fetch.return_value = factories.Annotation(shared=True)
        return fetch

    @pytest.fixture(autouse=True)
    def SocketFilter(self, patch):
        SocketFilter = patch("h.streamer.messages.SocketFilter")
        SocketFilter.matching.side_effect = lambda sockets, annotation: iter(sockets)
        return SocketFilter

    @pytest.fixture
    def no_matching_sockets(self, SocketFilter):
        SocketFilter.matching.side_effect = lambda sockets, annotation: iter(())

    @pytest.fixture
    def presenters(self, patch):
        return patch("h.streamer.messages.presenters")

    @pytest.fixture
    def AnnotationUserInfoFormatter(self, patch):
        return patch("h.streamer.messages.AnnotationUserInfoFormatter")

    @pytest.fixture
    def presenter_asdict(self, patch):
        return patch("h.streamer.messages.presenters.AnnotationJSONPresenter.asdict")

    @pytest.fixture
    def user_service(self, patch):
        return patch("h.streamer.messages.UserService")

    @pytest.fixture
    def links_service(self, patch):
        return patch("h.streamer.messages.LinksService")

    @pytest.fixture
    def groupfinder_service(self, patch):
        return patch("h.streamer.messages.GroupfinderService")

    @pytest.fixture
    def nipsa_service(self, patch):
        service = patch("h.streamer.messages.NipsaService")
        service.return_value.is_flagged.return_value = False
        return service

    @pytest.fixture
    def annotation_resource(self, patch):
        return patch("h.streamer.messages.AnnotationContext")

    @pytest.fixture
    def principals_allowed_by_permission(self, patch):
        return patch("h.streamer.messages.principals_allowed_by_permission")


class TestHandleUserEvent:
    def test_sends_session_change_when_joining_or_leaving_group(self):
        session_model = mock.Mock()
        message = {
            "type": "group-join",
            "userid": "amy",
            "group": "groupid",
            "session_model": session_model,
        }
        socket = FakeSocket("clientid")
        socket.authenticated_userid = "amy"

        messages.handle_user_event(message, [socket], None, None)

        assert socket.send_json_payloads[0] == {
            "type": "session-change",
            "action": "group-join",
            "model": session_model,
        }

    def test_no_send_when_socket_is_not_event_users(self):
        """Don't send session-change events if the event user is not the socket user."""
        message = {"type": "group-join", "userid": "amy", "group": "groupid"}
        socket = FakeSocket("clientid")
        socket.authenticated_userid = "bob"

        messages.handle_user_event(message, [socket], None, None)

        assert socket.send_json_payloads == []
