from h.security import Identity
from h.streamer import streamer, views


def test_websocket_view_adds_auth_state_to_environ(pyramid_request):
    pyramid_request.identity = Identity()
    pyramid_request.get_response = lambda _: None

    views.websocket_view(pyramid_request)
    env = pyramid_request.environ

    assert env["h.ws.identity"] == pyramid_request.identity


def test_websocket_view_adds_work_queue_to_environ(pyramid_request):
    pyramid_request.get_response = lambda _: None

    views.websocket_view(pyramid_request)
    env = pyramid_request.environ

    assert env["h.ws.streamer_work_queue"] == streamer.WORK_QUEUE
