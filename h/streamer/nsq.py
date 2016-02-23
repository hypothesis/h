# -*- coding: utf-8 -*-

import base64
from collections import namedtuple
import json
import logging
import random
import struct

from gevent.queue import Full

from h import queue
from h.api import auth
from h.api import storage
from h.streamer import websocket

log = logging.getLogger(__name__)

# NSQ message topics that the WebSocket server
# processes messages from
ANNOTATIONS_TOPIC = 'annotations'
USER_TOPIC = 'user'

# An incoming message from a subscribed NSQ topic
Message = namedtuple('Message', ['topic', 'payload'])


def process_nsq_topic(settings, topic, work_queue, raise_error=True):
    """
    Configure, start, and monitor a queue reader for the specified topic.

    This sets up a :py:class:`gnsq.Reader` to route messages from `topic` to
    the passed `work_queue`, and starts it. The reader should never return. If
    it does, this function will raise an exception.

    If `raise_error` is False, the function will not reraise errors from the
    queue reader.
    """
    channel = 'stream-{}#ephemeral'.format(_random_id())
    reader = queue.get_reader(settings, topic, channel)

    # The only thing queue readers do is put the incoming messages onto the
    # work queue.
    #
    # Note that this means that any errors occurring while handling the
    # messages will not result in requeues, but this is probably the best we
    # can do given that these messages fan out to our WebSocket clients, and we
    # can't easily know that we haven't already sent a requeued message out to
    # a particular client.
    def _handler(reader, message):
        try:
            work_queue.put(Message(topic=reader.topic, payload=message.body),
                           timeout=0.1)
        except Full:
            log.warn('Streamer work queue full! Unable to queue message from '
                     'NSQ having waited 0.1s: giving up.')

    reader.on_message.connect(receiver=_handler, weak=False)
    reader.start()

    # Reraise any exceptions raised by reader greenlets
    reader.join(raise_error=raise_error)

    # We should never get here: if we do, it means that the reader exited
    # without raising an exception, which doesn't make much sense.
    if raise_error:
        raise RuntimeError('Queue reader quit unexpectedly!')


def handle_message(message, topic_handlers=None):
    """
    Deserialize and process a message from the reader.

    For each message, `handler` is called with the deserialized message and a
    single :py:class:`h.streamer.WebSocket` instance, and should return the
    message to be sent to the client on that socket. The handler can return
    `None`, to signify that no message should be sent, or a JSON-serializable
    object. It is assumed that there is a 1:1 request-reply mapping between
    incoming messages and messages to be sent out over the websockets.
    """
    if topic_handlers is None:
        topic_handlers = {
            ANNOTATIONS_TOPIC: handle_annotation_event,
            USER_TOPIC: handle_user_event,
        }

    data = json.loads(message.payload)

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
