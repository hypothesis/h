# -*- coding: utf-8 -*-

import json
import logging
import weakref

import jsonschema
from pyramid.threadlocal import get_current_request
from ws4py.websocket import WebSocket as _WebSocket

from h.api import storage
from h.streamer import filter

log = logging.getLogger(__name__)


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

    def opened(self):
        # Release the database transaction
        self.request.tm.commit()

    def _expand_clauses(self, payload):
        for clause in payload['clauses']:
            if clause['field'] == '/uri':
                self._expand_uris(clause)

    def _expand_uris(self, clause):
        uris = clause['value']
        expanded = set()

        if not isinstance(uris, list):
            uris = [uris]

        # FIXME: this is a temporary hack to allow us to disable URI
        # equivalence support on the streamer while we debug a number of
        # issues related to connection pool exhaustion for the websocket
        # server.  -NS 2016-02-19
        if self.request.feature('ops_disable_streamer_uri_equivalence'):
            expanded.update(uris)
        else:
            for item in uris:
                expanded.update(storage.expand_uri(item))

        clause['value'] = list(expanded)

    def received_message(self, msg):
        with self.request.tm:
            self._process_message(msg)

    def _process_message(self, msg):
        try:
            data = json.loads(msg.data)
            msg_type = data.get('messageType', 'filter')

            if msg_type == 'filter':
                payload = data['filter']

                # Let's try to validate the schema
                jsonschema.validate(payload, filter.SCHEMA)

                # Add backend expands for clauses
                self._expand_clauses(payload)

                self.filter = filter.FilterHandler(payload)
            elif msg_type == 'client_id':
                self.client_id = data.get('value')
        except:
            # TODO: clean this up, catch specific errors, narrow the scope
            log.exception("Parsing filter: %s", msg)
            self.close()
            raise
