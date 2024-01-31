import copy
import json
import logging
import weakref
from collections import namedtuple

import jsonschema
from gevent.queue import Full
from ws4py.websocket import WebSocket as _WebSocket

from h.streamer.filter import FILTER_SCHEMA, SocketFilter

log = logging.getLogger(__name__)

# Mapping incoming message type to handler function. Handlers are added inline
# below.
MESSAGE_HANDLERS = {}


# An incoming message from a WebSocket client.
class Message(namedtuple("Message", ["socket", "payload"])):
    def reply(self, payload, ok=True):
        """
        Send a response to this message.

        Sends a reply message back to the client, with the passed `payload`
        and reporting status `ok`.
        """
        reply_to = self.payload.get("id")
        # Short-circuit if message is missing an ID or has a non-numeric ID.
        if not isinstance(reply_to, (int, float)):
            return
        data = copy.deepcopy(payload)
        data["ok"] = ok
        data["reply_to"] = reply_to
        self.socket.send_json(data)


class WebSocket(_WebSocket):
    # All instances of WebSocket, allowing us to iterate over open websockets
    instances = weakref.WeakSet()

    # Instance attributes
    client_id = None
    filter = None
    query = None
    identity = None

    debug = False
    """Enable debug logging for this connection."""

    def __init__(self, sock, protocols=None, extensions=None, environ=None):
        super().__init__(
            sock,
            protocols=protocols,
            extensions=extensions,
            environ=environ,
            heartbeat_freq=30.0,
        )

        self.debug = environ["h.ws.debug"]
        self.identity = environ["h.ws.identity"]

        self._work_queue = environ["h.ws.streamer_work_queue"]

    def __new__(cls, *_args, **_kwargs):
        instance = super(WebSocket, cls).__new__(cls)
        cls.instances.add(instance)
        return instance

    def received_message(self, message):
        if self.debug:
            log.info("Received message %s", message)

        try:
            payload = json.loads(message.data)
        except ValueError:
            if self.debug:
                log.warning("Failed to parse message %s", message)
            self.close(reason="invalid message format")
            return

        try:
            self._work_queue.put(Message(socket=self, payload=payload), timeout=0.1)
        except Full:  # pragma: no cover
            log.warning(
                "Streamer work queue full! Unable to queue message from "
                "WebSocket client having waited 0.1s: giving up."
            )

    def closed(self, code, reason=None):
        if self.debug:
            log.info("Closed connection code=%s reason=%s", code, reason)
        try:
            self.instances.remove(self)
        except KeyError:
            pass

    def send_json(self, payload):
        if self.debug:
            log.info("Sending message %s (terminated: %s)", payload, self.terminated)
        if not self.terminated:
            self.send(json.dumps(payload))


def handle_message(message, session=None):
    """
    Handle an incoming message from a client websocket.

    Receives a :py:class:`~h.streamer.websocket.Message` instance, which holds
    references to the :py:class:`~h.streamer.websocket.WebSocket` instance
    associated with the client connection, as well as the message payload.

    It updates state on the :py:class:`~h.streamer.websocket.WebSocket`
    instance in response to the message content.

    It may also passed a database session which *must* be used for any
    communication with the database.
    """
    if message.socket.debug:  # pragma: no cover
        log.info("Handling message %s", message.payload)

    payload = message.payload
    type_ = payload.get("type")

    # FIXME: This code is here to tolerate old and deprecated message formats.
    if type_ is None:  # pragma: no cover
        if "messageType" in payload and payload["messageType"] == "client_id":
            type_ = "client_id"
        if "filter" in payload:
            type_ = "filter"

    # N.B. MESSAGE_HANDLERS[None] handles both incorrect and missing message
    # types.
    handler = MESSAGE_HANDLERS.get(type_, MESSAGE_HANDLERS[None])
    handler(message, session=session)


def handle_client_id_message(message, session=None):  # pylint: disable=unused-argument
    """Answer to a client telling us its client ID."""
    if "value" not in message.payload:
        message.reply(
            {
                "type": "error",
                "error": {"type": "invalid_data", "description": '"value" is missing'},
            },
            ok=False,
        )
        return
    message.socket.client_id = message.payload["value"]


MESSAGE_HANDLERS["client_id"] = handle_client_id_message


def handle_filter_message(message, session=None):  # pylint: disable=unused-argument
    """Answer to a client updating its streamer filter."""
    if "filter" not in message.payload:
        message.reply(
            {
                "type": "error",
                "error": {"type": "invalid_data", "description": '"filter" is missing'},
            },
            ok=False,
        )
        return

    filter_ = message.payload["filter"]
    try:
        jsonschema.validate(filter_, FILTER_SCHEMA)
    except jsonschema.ValidationError:
        message.reply(
            {
                "type": "error",
                "error": {
                    "type": "invalid_data",
                    "description": "failed to parse filter",
                },
            },
            ok=False,
        )
        return

    SocketFilter.set_filter(message.socket, filter_)


MESSAGE_HANDLERS["filter"] = handle_filter_message


def handle_ping_message(message, session=None):  # pylint: disable=unused-argument
    """Reply to a client requesting a pong."""
    message.reply({"type": "pong"})


MESSAGE_HANDLERS["ping"] = handle_ping_message


def handle_whoami_message(message, session=None):  # pylint: disable=unused-argument
    """Reply to a client requesting information on its auth state."""

    message.reply(
        {
            "type": "whoyouare",
            "userid": (
                message.socket.identity.user.userid if message.socket.identity else None
            ),
        }
    )


MESSAGE_HANDLERS["whoami"] = handle_whoami_message


def handle_unknown_message(message, session=None):  # pylint: disable=unused-argument
    """Handle the message type being missing or not recognised."""
    type_ = json.dumps(message.payload.get("type"))
    message.reply(
        {
            "type": "error",
            "error": {
                "type": "invalid_type",
                "description": f"invalid message type: {type_}",
            },
        },
        ok=False,
    )


MESSAGE_HANDLERS[None] = handle_unknown_message
