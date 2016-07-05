# -*- coding: utf-8 -*-

from collections import namedtuple
import json
import logging
import weakref

from gevent.queue import Full
import jsonschema
from ws4py.websocket import WebSocket as _WebSocket

from h.api import storage
from h.streamer import filter

log = logging.getLogger(__name__)

# An incoming message from a WebSocket client.
Message = namedtuple('Message', ['socket', 'payload'])


class WebSocket(_WebSocket):
    # All instances of WebSocket, allowing us to iterate over open websockets
    instances = weakref.WeakSet()
    origins = []

    # Instance attributes
    client_id = None
    filter = None
    query = None

    def __init__(self, sock, protocols=None, extensions=None, environ=None):
        super(WebSocket, self).__init__(sock,
                                        protocols=protocols,
                                        extensions=extensions,
                                        environ=environ,
                                        heartbeat_freq=30.0)

        self.authenticated_userid = environ['h.ws.authenticated_userid']
        self.effective_principals = environ['h.ws.effective_principals']
        self.registry = environ['h.ws.registry']

        self._work_queue = environ['h.ws.streamer_work_queue']

    def __new__(cls, *args, **kwargs):
        instance = super(WebSocket, cls).__new__(cls, *args, **kwargs)
        cls.instances.add(instance)
        return instance

    def received_message(self, msg):
        try:
            self._work_queue.put(Message(socket=self, payload=msg.data),
                                 timeout=0.1)
        except Full:
            log.warn('Streamer work queue full! Unable to queue message from '
                     'WebSocket client having waited 0.1s: giving up.')

    def closed(self, code, reason=None):
        try:
            self.instances.remove(self)
        except KeyError:
            pass

    def send_json(self, payload):
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
    socket = message.socket

    data = json.loads(message.payload)

    try:
        msg_type = data.get('messageType', 'filter')

        if msg_type == 'filter':
            payload = data['filter']

            # Let's try to validate the schema
            jsonschema.validate(payload, filter.SCHEMA)

            if session is not None:
                # Add backend expands for clauses
                _expand_clauses(session, payload)

            socket.filter = filter.FilterHandler(payload)
        elif msg_type == 'client_id':
            socket.client_id = data.get('value')
    except:
        # TODO: clean this up, catch specific errors, narrow the scope
        log.exception("Parsing filter: %s", data)
        socket.close()
        raise


def _expand_clauses(session, payload):
    for clause in payload['clauses']:
        if clause['field'] == '/uri':
            _expand_uris(session, clause)


def _expand_uris(session, clause):
    uris = clause['value']
    expanded = set()

    if not isinstance(uris, list):
        uris = [uris]

    for item in uris:
        expanded.update(storage.expand_uri(session, item))

    clause['value'] = list(expanded)
