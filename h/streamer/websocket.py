# -*- coding: utf-8 -*-

from collections import namedtuple
import json
import logging
import weakref

from gevent.queue import Full
import jsonschema
from pyramid.threadlocal import get_current_request
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
    request = None
    query = None

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('heartbeat_freq', 30.0)
        super(WebSocket, self).__init__(*args, **kwargs)
        self.request = get_current_request()

    def __new__(cls, *args, **kwargs):
        instance = super(WebSocket, cls).__new__(cls, *args, **kwargs)
        cls.instances.add(instance)
        return instance

    def received_message(self, msg):
        work_queue = self.request.registry['streamer.work_queue']
        try:
            work_queue.put(Message(socket=self, payload=msg.data),
                           timeout=0.1)
        except Full:
            log.warn('Streamer work queue full! Unable to queue message from '
                     'WebSocket client having waited 0.1s: giving up.')

    def closed(self, code, reason=None):
        try:
            self.instances.remove(self)
        except KeyError:
            pass


def handle_message(message):
    socket = message.socket
    socket.request.feature.clear()

    data = json.loads(message.payload)

    try:
        msg_type = data.get('messageType', 'filter')

        if msg_type == 'filter':
            payload = data['filter']

            # Let's try to validate the schema
            jsonschema.validate(payload, filter.SCHEMA)

            # Add backend expands for clauses
            _expand_clauses(socket.request, payload)

            socket.filter = filter.FilterHandler(payload)
        elif msg_type == 'client_id':
            socket.client_id = data.get('value')
    except:
        # TODO: clean this up, catch specific errors, narrow the scope
        log.exception("Parsing filter: %s", data)
        socket.close()
        raise
    finally:
        # Ensure that we aren't holding onto any database connections.
        #
        # TODO: We really shouldn't be using socket.request.db at all, but
        # instead using the single session created by process_work_queue.
        socket.request.db.close()

def _expand_clauses(request, payload):
    for clause in payload['clauses']:
        if clause['field'] == '/uri':
            _expand_uris(request.db, clause)


def _expand_uris(session, clause):
    uris = clause['value']
    expanded = set()

    if not isinstance(uris, list):
        uris = [uris]

    for item in uris:
        expanded.update(storage.expand_uri(session, item))

    clause['value'] = list(expanded)
