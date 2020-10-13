from newrelic.agent import data_source_factory

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
        active_connections = len(WebSocket.instances)
        authenticated_connections = sum(
            1 for ws in WebSocket.instances if ws.authenticated_userid
        )

        yield f"{prefix}/ConnectionsActive", active_connections
        yield f"{prefix}/ConnectionsAuthenticated", authenticated_connections
        yield f"{prefix}/ConnectionsAnonymous", active_connections - authenticated_connections

    return generate_metrics
