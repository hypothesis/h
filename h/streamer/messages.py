import logging
from collections import namedtuple
from itertools import chain

import pyramid.scripting
from gevent.queue import Full
from pyramid.security import principals_allowed_by_permission

from h import presenters, realtime, storage
from h.formatters import AnnotationUserInfoFormatter
from h.realtime import Consumer
from h.services.groupfinder import GroupfinderService
from h.services.links import LinksService
from h.services.nipsa import NipsaService
from h.services.user import UserService
from h.streamer import websocket
from h.streamer.contexts import AnnotationNotificationContext
from h.streamer.filter import SocketFilter

log = logging.getLogger(__name__)


# An incoming message from a subscribed realtime consumer
Message = namedtuple("Message", ["topic", "payload"])


def process_messages(settings, routing_key, work_queue, raise_error=True):
    """
    Configure, start, and monitor a realtime consumer for the specified
    routing key.

    This sets up a :py:class:`h.realtime.Consumer` to route messages from
    `routing_key` to the passed `work_queue`, and starts it. The consumer
    should never return. If it does, this function will raise an exception.
    """

    def _handler(payload):
        try:
            message = Message(topic=routing_key, payload=payload)
            work_queue.put(message, timeout=0.1)
        except Full:
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
    except KeyError:
        raise RuntimeError(
            "Don't know how to handle message from topic: " "{}".format(message.topic)
        )

    # N.B. We iterate over a non-weak list of instances because there's nothing
    # to stop connections being added or dropped during iteration, and if that
    # happens Python will throw a "Set changed size during iteration" error.
    sockets = list(websocket.WebSocket.instances)

    # The `prepare` function sets the active registry which is an implicit
    # dependency of some of the authorization logic used to look up annotation
    # and group permissions.
    with pyramid.scripting.prepare(registry=registry):
        handler(message.payload, sockets, registry, session)


def handle_user_event(message, sockets, registry, session):
    # for session state change events, the full session model
    # is included so that clients can update themselves without
    # further API requests

    reply = None

    for socket in sockets:
        if socket.authenticated_userid != message["userid"]:
            continue

        if reply is None:
            reply = {
                "type": "session-change",
                "action": message["type"],
                "model": message["session_model"],
            }

        socket.send_json(reply)


def handle_annotation_event(message, sockets, registry, session):
    id_ = message["annotation_id"]
    annotation = storage.fetch_annotation(session, id_)

    if annotation is None:
        log.warning("received annotation event for missing annotation: %s", id_)
        return

    # Find connected clients which are interested in this annotation.
    matching_sockets = SocketFilter.matching(sockets, annotation)

    try:
        # Check to see if the generator has any items
        first_socket = next(matching_sockets)
    except StopIteration:
        # Nothing matched
        return

    # Create a generator which has the first socket back again
    matching_sockets = chain((first_socket,), matching_sockets)

    authority = registry.settings.get("h.authority", "localhost")
    base_url = registry.settings.get("h.app_url", "http://localhost:5000")

    resource = AnnotationNotificationContext(
        annotation,
        group_service=GroupfinderService(session, authority),
        links_service=LinksService(base_url, registry),
    )
    read_principals = principals_allowed_by_permission(resource, "read")
    reply = _generate_annotation_event(session, authority, message, resource)

    annotator_nipsad = NipsaService(session).is_flagged(annotation.userid)

    for socket in matching_sockets:
        # Don't send notifications back to the person who sent them
        if message["src_client_id"] == socket.client_id:
            continue

        # Only send NIPSA'd annotations to the author
        if annotator_nipsad and socket.authenticated_userid != annotation.userid:
            continue

        # Check whether client is authorized to read this annotation.
        if not set(read_principals).intersection(socket.effective_principals):
            continue

        socket.send_json(reply)


def _generate_annotation_event(session, authority, message, resource):
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
        user_service = UserService(authority, session)
        formatters = [AnnotationUserInfoFormatter(session, user_service)]
        payload = presenters.AnnotationJSONPresenter(
            resource, formatters=formatters
        ).asdict()

    return {
        "type": "annotation-notification",
        "options": {"action": message["action"]},
        "payload": [payload],
    }
