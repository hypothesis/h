import gevent
import newrelic.agent

from h.streamer import db
from h.streamer.websocket import WebSocket

PREFIX = "Custom/WebSocket"
METRICS_INTERVAL = 60


def websocket_metrics(queue):
    """
    Report metrics about the websocket service to New Relic.

    See https://docs.newrelic.com/docs/agents/python-agent/supported-features/python-custom-metrics.
    """

    connections_active = len(WebSocket.instances)
    connections_anonymous = sum(
        1 for ws in WebSocket.instances if not ws.authenticated_userid
    )

    # Allow us to tell the difference between reporting 0 and not reporting
    yield f"{PREFIX}/Alive", 1

    yield f"{PREFIX}/Connections/Active", connections_active
    yield f"{PREFIX}/Connections/Authenticated", connections_active - connections_anonymous
    yield f"{PREFIX}/Connections/Anonymous", connections_anonymous

    yield f"{PREFIX}/WorkQueueSize", queue.qsize()


def metrics_process(registry, queue):
    session = db.get_session(registry.settings)

    newrelic.agent.initialize()
    application = newrelic.agent.application()

    while True:
        with db.read_only_transaction(session):

            newrelic.agent.record_custom_metrics(
                websocket_metrics(queue), application=application
            )

        gevent.sleep(METRICS_INTERVAL)
