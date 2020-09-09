# -*- coding: utf-8 -*-

import logging
from collections import namedtuple
from itertools import chain

import pyramid.scripting
from gevent.queue import Full
from pyramid.security import principals_allowed_by_permission

from h import presenters, realtime, storage
from h.auth.util import translate_annotation_principals
from h.formatters import AnnotationUserInfoFormatter
from h.realtime import Consumer
from h.services.groupfinder import GroupfinderService
from h.services.links import LinksService
from h.services.nipsa import NipsaService
from h.services.user import UserService
from h.streamer import websocket
from h.streamer.filter import SocketFilter
from h.traversal import AnnotationContext

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
    consumer = Consumer(connection=conn, routing_key=routing_key, handler=_handler,)
    consumer.run()

    if raise_error:
        raise RuntimeError("Realtime consumer quit unexpectedly!")


def handle_message(message, settings, session, topic_handlers):
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
    handler(message.payload, sockets, settings, session)


def handle_annotation_event(message, sockets, settings, session):
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

    nipsa_service = NipsaService(session)
    user_nipsad = nipsa_service.is_flagged(annotation.userid)

    authority = settings.get("h.authority", "localhost")
    group_service = GroupfinderService(session, authority)
    user_service = UserService(authority, session)
    formatters = [AnnotationUserInfoFormatter(session, user_service)]

    for socket in matching_sockets:
        reply = _generate_annotation_event(
            message, socket, annotation, user_nipsad, group_service, formatters
        )
        if reply is None:
            continue
        socket.send_json(reply)


def handle_user_event(message, sockets, settings, session):
    for socket in sockets:
        reply = _generate_user_event(message, socket)
        if reply is None:
            continue
        socket.send_json(reply)


def _generate_annotation_event(
    message, socket, annotation, user_nipsad, group_service, formatters
):
    """
    Get message about annotation event `message` to be sent to `socket`.

    Inspects the embedded annotation event and decides whether or not the
    passed socket should receive notification of the event.

    Returns None if the socket should not receive any message about this
    annotation event, otherwise a dict containing information about the event.
    """
    action = message["action"]

    if action == "read":
        return None

    if message["src_client_id"] == socket.client_id:
        return None

    # Don't sent annotations from NIPSA'd users to anyone other than that
    # user.
    if user_nipsad and socket.authenticated_userid != annotation.userid:
        return None

    # The `prepare` function sets the active registry which is an implicit
    # dependency of some of the authorization logic used to look up annotation
    # and group permissions.
    with pyramid.scripting.prepare(registry=socket.registry):
        notification = {
            "type": "annotation-notification",
            "options": {"action": action},
        }

        base_url = socket.registry.settings.get("h.app_url", "http://localhost:5000")
        links_service = LinksService(base_url, socket.registry)
        resource = AnnotationContext(annotation, group_service, links_service)

        # Check whether client is authorized to read this annotation.
        read_principals = principals_allowed_by_permission(resource, "read")
        if not set(read_principals).intersection(socket.effective_principals):
            return None

        serialized = presenters.AnnotationJSONPresenter(
            resource, formatters=formatters
        ).asdict()

        notification["payload"] = [serialized]
        if action == "delete":
            notification["payload"] = [{"id": annotation.id}]
        return notification


def _generate_user_event(message, socket):
    """
    Get message about user event `message` to be sent to `socket`.

    Inspects the embedded user event and decides whether or not the passed
    socket should receive notification of the event.

    Returns None if the socket should not receive any message about this user
    event, otherwise a dict containing information about the event.
    """
    if socket.authenticated_userid != message["userid"]:
        return None

    # for session state change events, the full session model
    # is included so that clients can update themselves without
    # further API requests
    return {
        "type": "session-change",
        "action": message["type"],
        "model": message["session_model"],
    }
