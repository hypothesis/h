import logging
from collections import namedtuple
from itertools import chain

from gevent.queue import Full

from h import realtime
from h.realtime import Consumer
from h.security import Permission, identity_permits
from h.services.annotation_read import AnnotationReadService
from h.streamer import websocket
from h.streamer.contexts import request_context
from h.streamer.filter import SocketFilter
from h.traversal import AnnotationContext

log = logging.getLogger(__name__)


# An incoming message from a subscribed realtime consumer
Message = namedtuple("Message", ["topic", "payload"])


def process_messages(settings, routing_key, work_queue, raise_error=True):
    """
    Configure, start, and monitor a realtime consumer for the specified routing key.

    This sets up a :py:class:`h.realtime.Consumer` to route messages from
    `routing_key` to the passed `work_queue`, and starts it. The consumer
    should never return. If it does, this function will raise an exception.
    """

    def _handler(payload):
        message = Message(topic=routing_key, payload=payload)
        try:
            work_queue.put(message, timeout=0.1)
        except Full:  # pragma: no cover
            log.warning(
                "Streamer work queue full! Unable to queue message from "
                "h.realtime having waited 0.1s: giving up."
            )

    conn = realtime.get_connection(settings)
    consumer = Consumer(connection=conn, routing_key=routing_key, handler=_handler)
    consumer.run()

    if raise_error:
        raise RuntimeError("Realtime consumer quit unexpectedly!")


def handle_message(message, registry, session, topic_handlers):
    """
    Deserialize and process a message from the reader.

    For each message, `handler` is called with the deserialized message and a
    single :py:class:`h.streamer.WebSocket` instance, and should return the
    message to be sent to the client on that socket. The handler can return
    `None`, to signify that no message should be sent, or a JSON-serializable
    object. It is assumed that there is a 1:1 request-reply mapping between
    incoming messages and messages to be sent out over the websockets.
    """
    try:
        handler = topic_handlers[message.topic]
    except KeyError as err:
        raise RuntimeError(
            f"Don't know how to handle message from topic: {message.topic}"
        ) from err

    # N.B. We iterate over a non-weak list of instances because there's nothing
    # to stop connections being added or dropped during iteration, and if that
    # happens Python will throw a "Set changed size during iteration" error.
    sockets = list(websocket.WebSocket.instances)

    # The `prepare` function sets the active registry which is an implicit
    # dependency of some of the authorization logic used to look up annotation
    # and group permissions.
    with request_context(registry) as request:
        handler(message.payload, sockets, request, session)


def handle_user_event(message, sockets, _request, _session):
    # for session state change events, the full session model
    # is included so that clients can update themselves without
    # further API requests

    reply = None

    for socket in sockets:
        if not socket.identity or socket.identity.user.userid != message["userid"]:
            continue

        if reply is None:
            reply = {
                "type": "session-change",
                "action": message["type"],
                "model": message["session_model"],
            }

        socket.send_json(reply)


def handle_annotation_event(message, sockets, request, session):
    id_ = message["annotation_id"]
    annotation = request.find_service(AnnotationReadService).get_annotation_by_id(id_)

    if annotation is None:
        log.warning("received annotation event for missing annotation: %s", id_)
        return

    # Find connected clients which are interested in this annotation.
    matching_sockets = SocketFilter.matching(sockets, annotation, session)

    try:
        # Check to see if the generator has any items
        first_socket = next(matching_sockets)
    except StopIteration:
        # Nothing matched
        return

    # Create a generator which has the first socket back again
    matching_sockets = chain(  # pylint: disable=redefined-variable-type
        (first_socket,), matching_sockets
    )

    reply = _generate_annotation_event(request, message, annotation)

    annotator_nipsad = request.find_service(name="nipsa").is_flagged(annotation.userid)
    annotation_context = AnnotationContext(annotation)

    for socket in matching_sockets:
        # Don't send notifications back to the person who sent them
        if message["src_client_id"] == socket.client_id:
            continue

        # Only send NIPSA'd annotations to the author
        if (
            annotator_nipsad
            and socket.identity
            and socket.identity.user.userid != annotation.userid
        ):
            continue

        # Check whether client is authorized to read this annotation.
        if not identity_permits(
            socket.identity,
            annotation_context,
            Permission.Annotation.READ_REALTIME_UPDATES,
        ):
            continue

        socket.send_json(reply)


def _generate_annotation_event(request, message, annotation):
    """
    Get message about annotation event `message` to be sent to `socket`.

    Inspects the embedded annotation event and decides whether or not the
    passed socket should receive notification of the event.

    Returns None if the socket should not receive any message about this
    annotation event, otherwise a dict containing information about the event.
    """
    if message["action"] == "delete":
        payload = {"id": message["annotation_id"]}
    else:
        payload = request.find_service(name="annotation_json").present(annotation)

    return {
        "type": "annotation-notification",
        "options": {"action": message["action"]},
        "payload": [payload],
    }
