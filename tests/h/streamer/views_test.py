from h.streamer import streamer, views


def test_websocket_view_adds_auth_state_to_environ(pyramid_config, pyramid_request):
    pyramid_config.testing_securitypolicy("ragnar", groupids=["foo", "bar"])
    pyramid_request.get_response = lambda _: None

    views.websocket_view(pyramid_request)
    env = pyramid_request.environ

    assert env["h.ws.authenticated_userid"] == "ragnar"
    assert env["h.ws.effective_principals"] == pyramid_request.effective_principals


def test_websocket_view_adds_work_queue_to_environ(pyramid_request):
    pyramid_request.get_response = lambda _: None

    views.websocket_view(pyramid_request)
    env = pyramid_request.environ

    assert env["h.ws.streamer_work_queue"] == streamer.WORK_QUEUE
