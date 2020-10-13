from unittest.mock import create_autospec

import pytest
from h_matchers import Any

from h.streamer.metrics import websocket_metrics
from h.streamer.websocket import WebSocket


class TestWebsocketMetrics:
    def test_metrics(self, generate_metrics, sockets):
        sockets[0].authenticated_userid = "acct:jimsmith@hypothes.is"
        sockets[1].authenticated_userid = None
        sockets[2].authenticated_userid = None

        metrics = list(generate_metrics())

        expected_counts = [
            ("Custom/WebSocket/ConnectionsActive", 3),
            ("Custom/WebSocket/ConnectionsAuthenticated", 1),
            ("Custom/WebSocket/ConnectionsAnonymous", 2),
        ]
        assert metrics == Any.list.containing(expected_counts).only()

    @pytest.fixture
    def generate_metrics(self):
        # Work with the decorator from new relic to get the actual metrics
        # function inside.
        generate_metrics = websocket_metrics(settings={})["factory"]

        return generate_metrics(environ={})

    @pytest.fixture(autouse=True)
    def WebSocket(self, patch, sockets):
        WebSocket = patch("h.streamer.metrics.WebSocket")
        WebSocket.instances = sockets

        return WebSocket

    @pytest.fixture
    def sockets(self):
        return [create_autospec(WebSocket, instance=True) for _ in range(3)]
