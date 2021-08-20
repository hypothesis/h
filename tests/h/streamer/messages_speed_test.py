import pytest
from _datetime import datetime
from pyramid import security

from h.security import Identity
from h.streamer.app import create_app
from h.streamer.contexts import request_context
from h.streamer.messages import handle_annotation_event
from h.streamer.websocket import WebSocket
from tests.common.fixtures.elasticsearch import ELASTICSEARCH_INDEX, ELASTICSEARCH_URL


@pytest.mark.skip("Only of use during development")
class TestHandleAnnotationEventSpeed:  # pragma: no cover
    def test_load_request(self):
        ...
        # This is here just to flush out any first load costs

    @pytest.mark.parametrize("reps", (1, 16, 256, 4096))
    @pytest.mark.parametrize("action", ("create", "delete"))
    def test_speed(  # pylint: disable=too-many-arguments
        self, db_session, pyramid_request, socket, message, action, reps
    ):
        sockets = list(socket for _ in range(reps))
        message["action"] = action

        start = datetime.utcnow()
        handle_annotation_event(
            message=message,
            sockets=sockets,
            request=pyramid_request,
            session=db_session,
        )
        diff = datetime.utcnow() - start

        assert socket.send_json.count == reps

        millis = diff.seconds * 1000 + diff.microseconds / 1000
        print(
            f"{action} x {reps}: {millis} ms, {millis/reps} ms/item, {reps/millis*1000} items/sec"
        )

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation(shared=True)

    @pytest.fixture
    def pyramid_request(self, registry):
        with request_context(registry) as request:
            yield request

    @pytest.fixture
    def message(self, annotation):
        return {
            "annotation_id": annotation.id,
            "action": "create",
            "src_client_id": "1235",
        }

    @pytest.fixture(scope="session")
    def registry(self):
        settings = {
            "es.url": ELASTICSEARCH_URL,
            "es.index": ELASTICSEARCH_INDEX,
            "h.app_url": "http://example.com",
            "h.authority": "example.com",
            "secret_key": "notasecret",
            "sqlalchemy.url": "postgresql://postgres@localhost/htest",
        }

        return create_app(None, **settings).registry

    @pytest.fixture(autouse=True)
    def SocketFilter(self, patch):
        # We aren't interested in the speed of the socket filter, as that has
        # it's own speed tests
        SocketFilter = patch("h.streamer.messages.SocketFilter")
        SocketFilter.matching.side_effect = lambda sockets, annotation: iter(sockets)
        return SocketFilter

    @pytest.mark.usefixtures("registry")
    @pytest.fixture
    def socket(self):
        socket = WebSocket(
            sock=None,
            environ={
                "h.ws.identity": Identity(),
                "h.ws.effective_principals": [security.Everyone, "group:__world__"],
                "h.ws.streamer_work_queue": None,
            },
        )

        # We need to fake out the send reply function so it doesn't try and
        # actually do it. Using a mock here is _very_ slow in the numbers we are
        # doing
        def fake_send(_reply):
            fake_send.count += 1

        fake_send.count = 0
        socket.send_json = fake_send

        return socket
