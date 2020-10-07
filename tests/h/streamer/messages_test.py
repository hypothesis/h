from unittest.mock import Mock, create_autospec, sentinel

import pytest
from gevent.queue import Queue
from h_matchers import Any
from pyramid import security

from h.streamer import messages
from h.streamer.websocket import WebSocket


class TestProcessMessages:
    def test_it_creates_and_runs_a_consumer(self, Consumer, realtime, work_queue):
        settings = {}
        messages.process_messages(
            settings, "routing_key", work_queue, raise_error=False
        )

        realtime.get_connection.assert_called_once_with(settings)
        Consumer.assert_called_once_with(
            connection=realtime.get_connection.return_value,
            routing_key="routing_key",
            handler=Any(),
        )
        consumer = Consumer.return_value
        consumer.run.assert_called_once_with()

    def test_it_puts_message_on_queue(self, _handler, work_queue):
        _handler({"foo": "bar"})

        result = work_queue.get_nowait()
        assert result.topic == "routing_key"  # Set by _handler fixture
        assert result.payload == {"foo": "bar"}

    def test_it_handles_a_full_queue(self, _handler, work_queue):
        work_queue.put(messages.Message(topic="queue_is_full", payload={}))

        _handler({"foo": "bar"})

        result = work_queue.get_nowait()
        assert result.topic == "queue_is_full"

    def test_it_raises_if_the_consumer_exits(self, work_queue):
        with pytest.raises(RuntimeError):
            messages.process_messages({}, "routing_key", work_queue)

    @pytest.fixture
    def _handler(self, Consumer, work_queue):
        messages.process_messages({}, "routing_key", work_queue, raise_error=False)
        return Consumer.call_args[1]["handler"]

    @pytest.fixture(autouse=True)
    def Consumer(self, patch):
        return patch("h.streamer.messages.Consumer")

    @pytest.fixture(autouse=True)
    def realtime(self, patch):
        return patch("h.streamer.messages.realtime")

    @pytest.fixture
    def work_queue(self):
        return Queue(maxsize=1)


class TestHandleMessage:
    def test_calls_handler_with_list_of_sockets(self, websocket, registry):
        handler = Mock(return_value=None)
        session = sentinel.db_session
        message = messages.Message(topic="foo", payload={"foo": "bar"})
        websocket.instances = [sentinel.socket_1, sentinel.socket_2]

        messages.handle_message(
            message, registry, session, topic_handlers={"foo": handler}
        )

        handler.assert_called_once_with(
            message.payload, websocket.instances, registry, session
        )

    def test_it_raises_RuntimeError_for_bad_topics(self, registry):
        message = messages.Message(topic="unknown", payload={})
        topic_handlers = {"known": sentinel.handler}

        with pytest.raises(RuntimeError):
            messages.handle_message(
                message,
                registry,
                session=sentinel.db_session,
                topic_handlers=topic_handlers,
            )

    @pytest.fixture
    def registry(self, pyramid_request):
        return pyramid_request.registry

    @pytest.fixture
    def websocket(self, patch):
        return patch("h.streamer.websocket.WebSocket")


@pytest.mark.usefixtures("nipsa_service")
class TestHandleAnnotationEvent:
    def test_it_fetches_the_annotation(
        self, fetch_annotation, handle_annotation_event, session, message
    ):
        handle_annotation_event(message=message, session=session)

        fetch_annotation.assert_called_once_with(session, message["annotation_id"])

    def test_it_skips_notification_when_fetch_failed(
        self, fetch_annotation, handle_annotation_event
    ):
        fetch_annotation.return_value = None

        result = handle_annotation_event()

        assert result is None

    def test_it_initializes_groupfinder_service(
        self, groupfinder_service, handle_annotation_event, registry, session
    ):
        handle_annotation_event(registry=registry, session=session)

        groupfinder_service.assert_called_once_with(
            session, registry.settings["h.authority"]
        )

    def test_it_serializes_the_annotation(
        self,
        handle_annotation_event,
        fetch_annotation,
        links_service,
        groupfinder_service,
        AnnotationNotificationContext,
        AnnotationUserInfoFormatter,
        AnnotationJSONPresenter,
    ):
        handle_annotation_event()

        AnnotationNotificationContext.assert_called_once_with(
            fetch_annotation.return_value,
            groupfinder_service.return_value,
            links_service.return_value,
        )

        AnnotationJSONPresenter.assert_called_once_with(
            AnnotationNotificationContext.return_value,
            formatters=[AnnotationUserInfoFormatter.return_value],
        )
        assert AnnotationJSONPresenter.return_value.asdict.called

    @pytest.mark.parametrize("action", ["create", "update", "delete"])
    def test_notification_format(
        self, handle_annotation_event, action, message, socket, AnnotationJSONPresenter
    ):
        message["action"] = action

        handle_annotation_event(sockets=[socket])

        if action == "delete":
            expected_payload = {"id": message["annotation_id"]}
        else:
            expected_payload = AnnotationJSONPresenter.return_value.asdict.return_value

        socket.send_json.assert_called_once_with(
            {
                "payload": [expected_payload],
                "type": "annotation-notification",
                "options": {"action": action},
            }
        )

    def test_no_send_for_sender_socket(self, handle_annotation_event, socket, message):
        message["src_client_id"] = socket.client_id

        handle_annotation_event(message=message, sockets=[socket])

        socket.send_json.assert_not_called()

    def test_no_send_if_filter_does_not_match(
        self, handle_annotation_event, socket, SocketFilter
    ):
        SocketFilter.matching.side_effect = lambda sockets, annotation: iter(())
        handle_annotation_event(sockets=[socket])

        socket.send_json.assert_not_called()

    @pytest.mark.parametrize(
        "userid,can_see",
        (
            ("other_user", False),
            ("nipsaed_user", True),
        ),
    )
    def test_nipsaed_content_visibility(
        self,
        handle_annotation_event,
        userid,
        can_see,
        socket,
        nipsa_service,
        fetch_annotation,
    ):
        """Should return None if the annotation is from a NIPSA'd user."""
        nipsa_service.return_value.is_flagged.return_value = True
        fetch_annotation.return_value.userid = "nipsaed_user"
        socket.authenticated_userid = userid

        handle_annotation_event(sockets=[socket])

        assert bool(socket.send_json.call_count) == can_see

    @pytest.mark.parametrize(
        "user_principals,can_see",
        (
            [[], False],
            [["wrong_principal"], False],
            [["principal"], True],
            [["principal", "user_noise"], True],
        ),
    )
    def test_visibility_is_based_on_acl(
        self,
        handle_annotation_event,
        user_principals,
        can_see,
        AnnotationNotificationContext,
        principals_allowed_by_permission,
        socket,
    ):
        principals_allowed_by_permission.return_value = ["principal", "acl_noise"]
        socket.effective_principals = user_principals

        handle_annotation_event(sockets=[socket])

        principals_allowed_by_permission.assert_called_with(
            AnnotationNotificationContext.return_value, "read"
        )
        assert bool(socket.send_json.call_count) == can_see

    @pytest.fixture
    def handle_annotation_event(self, message, socket, registry, session):
        def handle_annotation_event(
            message=message, sockets=None, registry=registry, session=session
        ):
            if sockets is None:
                sockets = [socket]

            return messages.handle_annotation_event(message, sockets, registry, session)

        return handle_annotation_event

    @pytest.fixture
    def registry(self, pyramid_request):
        registry = pyramid_request.registry
        registry.settings = {
            "h.app_url": "http://streamer",
            "h.authority": "example.org",
        }

        return registry

    @pytest.fixture
    def session(self):
        return sentinel.db_session

    @pytest.fixture
    def message(self, fetch_annotation):
        return {
            # This is a bit backward from how things really work, but it
            # ensures the id we look up gives us an annotation that matches
            "annotation_id": fetch_annotation.return_value.id,
            "action": "update",
            "src_client_id": "source_socket",
        }

    @pytest.fixture(autouse=True)
    def fetch_annotation(self, factories, patch):
        fetch = patch("h.streamer.messages.storage.fetch_annotation")
        fetch.return_value = factories.Annotation()
        return fetch

    @pytest.fixture
    def principals_allowed_by_permission(self, patch):
        return patch("h.streamer.messages.principals_allowed_by_permission")

    @pytest.fixture
    def AnnotationUserInfoFormatter(self, patch):
        return patch("h.streamer.messages.AnnotationUserInfoFormatter")

    @pytest.fixture
    def AnnotationNotificationContext(self, patch):
        return patch("h.streamer.messages.AnnotationNotificationContext")

    @pytest.fixture(autouse=True)
    def AnnotationJSONPresenter(self, patch):
        return patch("h.streamer.messages.presenters.AnnotationJSONPresenter")

    @pytest.fixture(autouse=True)
    def SocketFilter(self, patch):
        SocketFilter = patch("h.streamer.messages.SocketFilter")
        SocketFilter.matching.side_effect = lambda sockets, annotation: iter(sockets)
        return SocketFilter

    @pytest.fixture(autouse=True)
    def user_service(self, patch):
        return patch("h.streamer.messages.UserService")

    @pytest.fixture(autouse=True)
    def links_service(self, patch):
        return patch("h.streamer.messages.LinksService")

    @pytest.fixture(autouse=True)
    def groupfinder_service(self, patch):
        return patch("h.streamer.messages.GroupfinderService")

    @pytest.fixture
    def nipsa_service(self, patch):
        service = patch("h.streamer.messages.NipsaService")
        service.return_value.is_flagged.return_value = False
        return service


class TestHandleUserEvent:
    def test_sends_session_change_when_joining_or_leaving_group(self, socket):
        session_model = Mock()
        message = {
            "type": "group-join",
            "userid": "amy",
            "group": "groupid",
            "session_model": session_model,
        }
        socket.authenticated_userid = "amy"

        messages.handle_user_event(message, [socket], None, None)

        socket.send_json.assert_called_once_with(
            {
                "type": "session-change",
                "action": "group-join",
                "model": session_model,
            }
        )

    def test_no_send_when_socket_is_not_event_users(self, socket):
        """Don't send session-change events if the event user is not the socket user."""
        message = {"type": "group-join", "userid": "amy", "group": "groupid"}
        socket.authenticated_userid = "bob"

        messages.handle_user_event(message, [socket], None, None)

        socket.send_json.assert_not_called()


@pytest.fixture
def socket():
    socket = create_autospec(WebSocket, instance=True)
    socket.effective_principals = [security.Everyone, "group:__world__"]
    return socket
