from unittest.mock import create_autospec

import pytest
from h_matchers import Any

from h.streamer.metrics import websocket_metrics
from h.streamer.websocket import WebSocket


class TestWebsocketMetrics:
    def test_it_records_socket_metrics(self, generate_metrics, sockets):
        sockets[0].authenticated_userid = "acct:jimsmith@hypothes.is"
        sockets[1].authenticated_userid = None
        sockets[2].authenticated_userid = None

        metrics = generate_metrics()

        assert list(metrics) == Any.list.containing(
            [
                ("Custom/WebSocket/Connections/Active", 3),
                ("Custom/WebSocket/Connections/Authenticated", 1),
                ("Custom/WebSocket/Connections/Anonymous", 2),
            ]
        )

    @pytest.mark.parametrize("size", (1, 5))
    def test_it_records_work_queue_metric(self, generate_metrics, WORK_QUEUE, size):
        WORK_QUEUE.qsize.return_value = size

        metrics = generate_metrics()

        assert list(metrics) == Any.list.containing(
            [("Custom/WebSocket/WorkQueueSize", size)]
        )

    def test_it_records_alive_metric(self, generate_metrics):
        metrics = generate_metrics()

        assert list(metrics) == Any.list.containing([("Custom/WebSocket/Alive", 1)])

    @pytest.fixture
    def generate_metrics(self):
        # Work with the decorator from new relic to get the actual metrics
        # function inside.
        generate_metrics = websocket_metrics(settings={})["factory"]

        return generate_metrics(environ={})

    @pytest.fixture
    def sockets(self):
        sockets = [create_autospec(WebSocket, instance=True) for _ in range(3)]
        for socket in sockets:
            socket.authenticated_userid = None

        return sockets

    @pytest.fixture(autouse=True)
    def WebSocket(self, patch, sockets):
        WebSocket = patch("h.streamer.metrics.WebSocket")
        WebSocket.instances = sockets

        return WebSocket

    @pytest.fixture
    def WORK_QUEUE(self, patch):
        return patch("h.streamer.metrics.WORK_QUEUE")
