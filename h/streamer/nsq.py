# -*- coding: utf-8 -*-

import base64
import functools
import json
import logging
import random
import struct

from h import queue
from h.api import auth
from h.api import storage
from h.streamer import websocket

log = logging.getLogger(__name__)

# NSQ message topics that the WebSocket server
# processes messages from
ANNOTATIONS_TOPIC = 'annotations'
USER_TOPIC = 'user'


def process_queue(settings, topic, handler):
    """
    Configure, start, and monitor a queue reader for the specified topic.

    This sets up a :py:class:`gnsq.Reader` to route messages from `topic` to
    `handler`, and starts it. The reader should never return. If it does, this
    fact is logged and the function returns.
    """
    channel = 'stream-{}#ephemeral'.format(_random_id())
    receiver = functools.partial(process_message, handler)
    reader = queue.get_reader(settings, topic, channel)
    reader.on_message.connect(receiver=receiver, weak=False)
    reader.start(block=True)

    # We should never get here. If we do, it's because a reader thread has
    # prematurely quit.
    log.error("queue reader for topic '%s' exited: killing reader", topic)
    reader.close()


def process_message(handler, reader, message):
    """
    Deserialize and process a message from the reader.

    For each message, `handler` is called with the deserialized message and a
    single :py:class:`h.streamer.WebSocket` instance, and should return the
    message to be sent to the client on that socket. The handler can return
    `None`, to signify that no message should be sent, or a JSON-serializable
    object. It is assumed that there is a 1:1 request-reply mapping between
    incoming messages and messages to be sent out over the websockets.

    Any exceptions thrown by this function or by `handler` will be caught by
    :py:class:`gnsq.Reader` and the message will be requeued as a result.
    """
    data = json.loads(message.body)

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
    annotation = storage.annotation_from_dict(message['annotation'])

    if action == 'read':
        return None

    if message['src_client_id'] == socket.client_id:
        return None

    if annotation.get('nipsa') and (
            socket.request.authenticated_userid != annotation.get('user', '')):
        return None

    if not _authorized_to_read(socket.request, annotation):
        return None

    # We don't send anything until we have received a filter from the client
    if socket.filter is None:
        return None

    if not socket.filter.match(annotation, action):
        return None

    return {
        'payload': [annotation],
        'type': 'annotation-notification',
        'options': {'action': action},
    }


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


def _authorized_to_read(request, annotation):
    """Return True if the passed request is authorized to read the annotation.

    If the annotation belongs to a private group, this will return False if the
    authenticated user isn't a member of that group.
    """
    # TODO: remove this when we've diagnosed this issue
    if ('permissions' not in annotation or
            'read' not in annotation['permissions']):
        request.sentry.captureMessage(
            'streamer received annotation lacking valid permissions',
            level='warn',
            extra={
                'id': annotation['id'],
                'permissions': json.dumps(annotation.get('permissions')),
            })

    read_permissions = annotation.get('permissions', {}).get('read', [])
    read_principals = auth.translate_annotation_principals(read_permissions)
    if set(read_principals).intersection(request.effective_principals):
        return True
    return False


def _random_id():
    """Generate a short random string"""
    data = struct.pack('Q', random.getrandbits(64))
    return base64.urlsafe_b64encode(data).strip(b'=')
