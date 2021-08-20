from unittest.mock import create_autospec

import pytest
from pyramid import security

from h.security import Identity
from h.streamer.websocket import WebSocket


@pytest.fixture
def socket(factories):
    socket = create_autospec(WebSocket, instance=True)
    socket.effective_principals = [security.Everyone, "group:__world__"]
    socket.identity = Identity(user=factories.User())

    return socket
