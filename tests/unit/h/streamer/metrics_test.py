from unittest.mock import create_autospec

import pytest
from gevent.pool import Pool
from gevent.queue import Queue
from h_matchers import Any

from h.security import Identity
from h.streamer.metrics import websocket_metrics
from h.streamer.websocket import WebSocket


class TestWebsocketMetrics:
    def test_it_records_socket_metrics(self, generate_metrics, sockets):
        sockets[0].identity = Identity()

        metrics = generate_metrics()

        assert list(metrics) == Any.list.containing(
            [
                ("Custom/WebSocket/Connections/Active", 3),
                ("Custom/WebSocket/Connections/Authenticated", 1),
                ("Custom/WebSocket/Connections/Anonymous", 2),
            ]
        )

    @pytest.mark.parametrize("size", (1, 5))
    def test_it_records_work_queue_metric(self, generate_metrics, queue, size):
        queue.qsize.return_value = size

        metrics = generate_metrics()

        assert list(metrics) == Any.list.containing(
            [("Custom/WebSocket/WorkQueueSize", size)]
        )

    def test_it_records_alive_metric(self, generate_metrics):
        metrics = generate_metrics()

        assert list(metrics) == Any.list.containing([("Custom/WebSocket/Alive", 1)])

    def test_it_records_worker_metrics(self, generate_metrics, server_instance):
        server_instance.connection_pool.size = 4096
        server_instance.connection_pool.free_count.return_value = 1024

        metrics = generate_metrics()

        assert list(metrics) == Any.list.containing(
            [
                ("Custom/WebSocket/Worker/Pool/MaxSize", 4096),
                ("Custom/WebSocket/Worker/Pool/Free", 1024),
                ("Custom/WebSocket/Worker/Pool/Used", 4096 - 1024),
            ]
        )

    @pytest.fixture
    def generate_metrics(self, queue):
        return lambda: websocket_metrics(queue)

    @pytest.fixture
    def queue(self):
        return create_autospec(Queue, instance=True, spec_set=True)

    @pytest.fixture
    def sockets(self):
        sockets = [create_autospec(WebSocket, instance=True) for _ in range(3)]
        for socket in sockets:
            socket.identity = None

        return sockets

    @pytest.fixture(autouse=True)
    def WebSocket(self, patch, sockets):
        WebSocket = patch("h.streamer.metrics.WebSocket")
        WebSocket.instances = sockets

        return WebSocket

    @pytest.fixture
    def server_instance(self, patch):
        WSGIServer = patch("h.streamer.metrics.WSGIServer")

        server_instance = WSGIServer()
        # Not sure why autospec doesn't pick any of this up, but it doesn't
        server_instance.connection_pool = create_autospec(Pool, instance=True)

        # Real instances register themselves with the class
        WSGIServer.instances = [server_instance]

        return server_instance
