# -*- coding: utf-8 -*-

from collections import namedtuple
import json
import logging

from gevent.queue import Full

from h import realtime
from h.realtime import Consumer
from h.api import presenters
from h.api import storage
from h.auth.util import translate_annotation_principals
from h.streamer import websocket
import h.sentry

log = logging.getLogger(__name__)


# An incoming message from a subscribed realtime consumer
Message = namedtuple('Message', ['topic', 'payload'])


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
            log.warn('Streamer work queue full! Unable to queue message from '
                     'h.realtime having waited 0.1s: giving up.')

    conn = realtime.get_connection(settings)
    sentry_client = h.sentry.get_client(settings)
    consumer = Consumer(connection=conn,
                        routing_key=routing_key,
                        handler=_handler, sentry_client=sentry_client)
    consumer.run()

    if raise_error:
        raise RuntimeError('Realtime consumer quit unexpectedly!')


def handle_message(message, topic_handlers):
    """
    Deserialize and process a message from the reader.

    For each message, `handler` is called with the deserialized message and a
    single :py:class:`h.streamer.WebSocket` instance, and should return the
    message to be sent to the client on that socket. The handler can return
    `None`, to signify that no message should be sent, or a JSON-serializable
    object. It is assumed that there is a 1:1 request-reply mapping between
    incoming messages and messages to be sent out over the websockets.
    """
    data = message.payload

    try:
        handler = topic_handlers[message.topic]
    except KeyError:
        raise RuntimeError("Don't know how to handle message from topic: "
                           "{}".format(message.topic))

    # N.B. We iterate over a non-weak list of instances because there's nothing
    # to stop connections being added or dropped during iteration, and if that
    # happens Python will throw a "Set changed size during iteration" error.
    sockets = list(websocket.WebSocket.instances)
    for socket in sockets:
        reply = handler(data, socket)
        if reply is None:
            continue
        if not socket.terminated:
            socket.send(json.dumps(reply))


def handle_annotation_event(message, socket):
    """
    Get message about annotation event `message` to be sent to `socket`.

    Inspects the embedded annotation event and decides whether or not the
    passed socket should receive notification of the event.

    Returns None if the socket should not receive any message about this
    annotation event, otherwise a dict containing information about the event.
    """
    action = message['action']

    if action == 'read':
        return None

    if message['src_client_id'] == socket.client_id:
        return None

    # We don't send anything until we have received a filter from the client
    if socket.filter is None:
        return None

    notification = {
        'type': 'annotation-notification',
        'options': {'action': action},
    }
    id_ = message['annotation_id']

    # Return early when action is delete
    serialized = None
    if action == 'delete':
        serialized = message['annotation_dict']
    else:
        annotation = storage.fetch_annotation(socket.request.db, id_)
        if annotation is None:
            return None

        serialized = presenters.AnnotationJSONPresenter(
            socket.request, annotation).asdict()

    userid = serialized.get('user')
    nipsa_service = socket.request.find_service(name='nipsa')
    if nipsa_service.is_flagged(userid) and socket.request.authenticated_userid != userid:
        return None

    permissions = serialized.get('permissions')
    if not _authorized_to_read(socket.request, permissions):
        return None

    if not socket.filter.match(serialized, action):
        return None

    notification['payload'] = [serialized]
    if action == 'delete':
        notification['payload'] = [{'id': id_}]
    return notification


def handle_user_event(message, socket):
    """
    Get message about user event `message` to be sent to `socket`.

    Inspects the embedded user event and decides whether or not the passed
    socket should receive notification of the event.

    Returns None if the socket should not receive any message about this user
    event, otherwise a dict containing information about the event.
    """
    if socket.request.authenticated_userid != message['userid']:
        return None

    # for session state change events, the full session model
    # is included so that clients can update themselves without
    # further API requests
    return {
        'type': 'session-change',
        'action': message['type'],
        'model': message['session_model']
    }


def _authorized_to_read(request, permissions):
    """Return True if the passed request is authorized to read the annotation.

    If the annotation belongs to a private group, this will return False if the
    authenticated user isn't a member of that group.
    """
    read_permissions = permissions.get('read', [])
    read_principals = translate_annotation_principals(read_permissions)
    if set(read_principals).intersection(request.effective_principals):
        return True
    return False
