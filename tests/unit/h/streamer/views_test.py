import pytest

from h.security import Identity
from h.streamer import streamer, views


class TestWebsocketView:
    def test_it_adds_auth_state_to_environ(self, pyramid_request, pyramid_config):
        pyramid_config.testing_securitypolicy(identity=Identity())

        views.websocket_view(pyramid_request)

        assert pyramid_request.environ["h.ws.identity"] == pyramid_request.identity

    def test_it_adds_work_queue_to_environ(self, pyramid_request):
        views.websocket_view(pyramid_request)

        assert (
            pyramid_request.environ["h.ws.streamer_work_queue"] == streamer.WORK_QUEUE
        )

    def test_debug_mode_is_disabled_by_default(self, pyramid_request):
        views.websocket_view(pyramid_request)
        assert pyramid_request.environ["h.ws.debug"] is False

    def test_enable_debug_mode(self, pyramid_request):
        pyramid_request.params["debug"] = "1"
        views.websocket_view(pyramid_request)
        assert pyramid_request.environ["h.ws.debug"] is True

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.get_response = lambda _: None

        return pyramid_request
