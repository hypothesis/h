import gevent
import newrelic.agent
from pkg_resources import resource_filename

from h.streamer import db
from h.streamer.websocket import WebSocket
from h.streamer.worker import WSGIServer

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

    # There really only should be one server per instance
    for server in WSGIServer.instances:
        pool = server.connection_pool
        free = pool.free_count()

        # We expect these values to track active connections exactly, so it's
        # either pointless if they do / very interesting if they don't.
        yield f"{PREFIX}/Worker/Pool/MaxSize", pool.size
        yield f"{PREFIX}/Worker/Pool/Free", free
        yield f"{PREFIX}/Worker/Pool/Used", pool.size - free


def metrics_process(registry, queue):  # pragma: no cover
    session = db.get_session(registry.settings)

    newrelic.agent.initialize(
        config_file=resource_filename("h.streamer", "conf/newrelic.ini")
    )
    newrelic.agent.register_application(timeout=5)
    application = newrelic.agent.application()

    while True:
        with db.read_only_transaction(session):
            application.record_custom_metrics(websocket_metrics(queue))

        gevent.sleep(METRICS_INTERVAL)
