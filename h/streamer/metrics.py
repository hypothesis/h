from newrelic.agent import data_source_factory

from h.streamer.streamer import WORK_QUEUE
from h.streamer.websocket import WebSocket


@data_source_factory(name="WebSocket Metrics")
def websocket_metrics(_settings, _environ):
    """
    A New Relic metric data source which provides metrics about WebSocket
    connections.

    See https://docs.newrelic.com/docs/agents/python-agent/supported-features/python-custom-metrics.
    """

    prefix = "Custom/WebSocket"

    def generate_metrics():
        connections_active = len(WebSocket.instances)
        connections_anonymous = sum(
            1 for ws in WebSocket.instances if not ws.authenticated_userid
        )

        yield f"{prefix}/Connections/Active", connections_active
        yield f"{prefix}/Connections/Authenticated", connections_active - connections_anonymous
        yield f"{prefix}/Connections/Anonymous", connections_anonymous

        yield f"{prefix}/WorkQueueSize", WORK_QUEUE.qsize()

    return generate_metrics
