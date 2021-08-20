from unittest.mock import PropertyMock

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

    def test_it_preloads_groups(self, pyramid_request, pyramid_config, factories):
        user = factories.User.build()
        groups = PropertyMock()
        type(user).groups = groups
        pyramid_config.testing_securitypolicy(identity=Identity(user=user))

        views.websocket_view(pyramid_request)

        groups.assert_called_once_with()

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.get_response = lambda _: None

        return pyramid_request
