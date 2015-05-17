# -*- coding: utf-8 -*-
import base64
import copy
import json
import logging
import operator
import random
import re
import struct
import unicodedata
import weakref

import gevent
import gevent.queue
from jsonpointer import resolve_pointer
from jsonschema import validate
from pyramid.config import aslist
from pyramid.httpexceptions import HTTPBadRequest, HTTPForbidden
from pyramid.threadlocal import get_current_request
import transaction
from ws4py.exc import HandshakeError
from ws4py.websocket import WebSocket as _WebSocket
from ws4py.server.wsgiutils import WebSocketWSGIApplication

from .api.auth import get_user  # FIXME: should not import from .api
from annotator import document
from .models import Annotation

log = logging.getLogger(__name__)


def uni_fold(text):
    # Convert str to unicode
    if isinstance(text, str):
        text = unicode(text, "utf-8")

    # Do not touch other types
    if not isinstance(text, unicode):
        return text

    text = text.lower()
    text = unicodedata.normalize('NFKD', text)
    return u"".join([c for c in text if not unicodedata.combining(c)])

filter_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "optional": True},
        "match_policy": {
            "type": "string",
            "enum": ["include_any", "include_all",
                     "exclude_any", "exclude_all"]
        },
        "actions": {
            "create": {"type": "boolean", "default":  True},
            "update": {"type": "boolean", "default":  True},
            "delete": {"type": "boolean", "default":  True},
        },
        "clauses": {
            "type": "array",
            "items": {
                "field": {"type": "string", "format": "json-pointer"},
                "operator": {
                    "type": "string",
                    "enum": ["equals", "matches", "lt", "le", "gt", "ge",
                             "one_of", "first_of", "match_of",
                             "lene", "leng", "lenge", "lenl", "lenle"]
                },
                "value": "object",
                "options": {"type": "object", "default": {}}
            }
        },
    },
    "required": ["match_policy", "clauses", "actions"]
}

len_operators = {
    "lene": "=",
    "leng": ">",
    "lenge": ">=",
    "lenl": "<",
    "lenle": "<="
}


class FilterToElasticFilter(object):
    def __init__(self, filter_json, request):
        self.request = request
        self.filter = filter_json
        self.query = {
            "sort": [
                {"updated": {"order": "desc"}}
            ],
            "query": {
                "bool": {
                    "minimum_number_should_match": 1}}}
        self.filter_scripts_to_add = []

        if len(self.filter['clauses']):
            clauses = self.convert_clauses(self.filter['clauses'])
            # apply match policy
            policy = getattr(self, self.filter['match_policy'])
            policy(self.query['query']['bool'], clauses)
        else:
            self.query['query'] = {"match_all": {}}

        if len(self.filter_scripts_to_add):
            if 'filter' not in self.query:
                self.query['filter'] = {}
            scripts = ' AND '.join(self.filter_scripts_to_add)
            self.query['filter']['script'] = '"script": ' + scripts

    @staticmethod
    def equals(field, value):
        if isinstance(value, list):
            return {"terms": {field: value}}
        else:
            return {"term": {field: value}}

    @staticmethod
    def one_of(field, value):
        if isinstance(value, list):
            return {"terms": {field: value}}
        else:
            return {"term": {field: value}}

    @staticmethod
    def first_of(field, value):
        if isinstance(value, list):
            return {"terms": {field: value}}
        else:
            return {"term": {field: value}}

    @staticmethod
    def match_of(field, value):
        if isinstance(value, list):
            return {"terms": {field: value}}
        else:
            return {"term": {field: value}}

    @staticmethod
    def matches(field, value):
        if isinstance(value, list):
            return {"terms": {field: value}}
        else:
            return {"term": {field: value}}

    @staticmethod
    def lt(field, value):
        return {"range": {field: {"lt": value}}}

    @staticmethod
    def le(field, value):
        return {"range": {field: {"lte": value}}}

    @staticmethod
    def gt(field, value):
        return {"range": {field: {"gt": value}}}

    @staticmethod
    def ge(field, value):
        return {"range": {field: {"gte": value}}}

    @staticmethod
    def _query_string_query(field, value):
        # Generate query_string query
        escaped_value = re.escape(value)
        return {
            "query_string": {
                "query": "*" + escaped_value + "*",
                "fields": [field]
            }
        }

    @staticmethod
    def _match_query(es, field, value):
        cutoff_freq = None
        and_or = 'and'
        if es:
            if 'cutoff_frequency' in es:
                cutoff_freq = es['cutoff_frequency']
            if 'and_or' in es:
                and_or = es['and_or']
        message = {
            "query": value,
            "operator": and_or
        }
        if cutoff_freq:
            message['cutoff_frequency'] = cutoff_freq
        return {"match": {field: message}}

    @staticmethod
    def _multi_match_query(es, value):
        and_or = es['and_or'] if 'and_or' in es else 'and'
        match_type = None
        if 'match_type' in es:
            match_type = es['match_type']
        message = {
            "query": value,
            "operator": and_or,
            "type": match_type,
            "fields": es['fields']
        }
        return {"multi_match": message}

    def convert_clauses(self, clauses):
        new_clauses = []
        for clause in clauses:
            if isinstance(clause['field'], list):
                field = []
                for f in clause['field']:
                    field.append(f[1:].replace('/', '.'))
            else:
                field = clause['field'][1:].replace('/', '.')
            es = clause['options']['es'] if 'es' in clause['options'] else None
            if es:
                query_type = es.get('query_type', 'simple')
            else:
                query_type = 'match'

            if isinstance(clause['value'], list):
                value = [x.lower() for x in clause['value']]
            else:
                value = clause['value'].lower()

            if query_type == 'query_string':
                new_clause = self._query_string_query(field, value)
            elif query_type == 'match':
                new_clause = self._match_query(es, field, value)
            elif query_type == 'multi_match':
                new_clause = self._multi_match_query(es, value)
            elif clause['operator'][0:2] == 'len':
                script = "doc['%s'].values.length %s %s" % (
                    field,
                    len_operators[clause['operator']],
                    clause[value]
                )
                self.filter_scripts_to_add.append(script)
            else:
                new_clause = getattr(self, clause['operator'])(field, value)

            new_clauses.append(new_clause)
        return new_clauses

    @staticmethod
    def _policy(oper, target, clauses):
        target[oper] = []
        for clause in clauses:
            target[oper].append(clause)

    def include_any(self, target, clauses):
        self._policy('should', target, clauses)

    def include_all(self, target, clauses):
        self._policy('must', target, clauses)

    def exclude_any(self, target, clauses):
        self._policy('must_not', target, clauses)

    def exclude_all(self, target, clauses):
        target['must_not'] = {"bool": {}}
        self._policy('must', target['must_not']['bool'], clauses)


def first_of(a, b):
    return a[0] == b
setattr(operator, 'first_of', first_of)


def match_of(a, b):
    for subb in b:
        if subb in a:
            return True
    return False
setattr(operator, 'match_of', match_of)


def lene(a, b):
    return len(a) == b
setattr(operator, 'lene', lene)


def leng(a, b):
    return len(a) > b
setattr(operator, 'leng', leng)


def lenge(a, b):
    return len(a) >= b
setattr(operator, 'lenge', lenge)


def lenl(a, b):
    return len(a) < b
setattr(operator, 'lenl', lenl)


def lenle(a, b):
    return len(a) <= b
setattr(operator, 'lenle', lenle)


class FilterHandler(object):
    def __init__(self, filter_json):
        self.filter = filter_json

    # operators
    operators = {
        'equals': 'eq',
        'matches': 'contains',
        'lt': 'lt',
        'le': 'le',
        'gt': 'gt',
        'ge': 'ge',
        'one_of': 'contains',
        'first_of': 'first_of',
        'match_of': 'match_of',
        'lene': 'lene',
        'leng': 'leng',
        'lenge': 'lenge',
        'lenl': 'lenl',
        'lenle': 'lenle',
    }

    def evaluate_clause(self, clause, target):
        if isinstance(clause['field'], list):
            for field in clause['field']:
                copied = copy.deepcopy(clause)
                copied['field'] = field
                result = self.evaluate_clause(copied, target)
                if result:
                    return True
            return False
        else:
            field_value = resolve_pointer(target, clause['field'], None)
            if field_value is None:
                return False

            cval = clause['value']
            fval = field_value

            if isinstance(cval, list):
                tval = []
                for cv in cval:
                    tval.append(uni_fold(cv))
                cval = tval
            else:
                cval = uni_fold(cval)

            if isinstance(fval, list):
                tval = []
                for fv in fval:
                    tval.append(uni_fold(fv))
                fval = tval
            else:
                fval = uni_fold(fval)

            reversed_order = False
            # Determining operator order
            # Normal order: field_value, clause['value']
            # i.e. condition created > 2000.01.01
            # Here clause['value'] = '2001.01.01'.
            # The field_value is target['created']
            # So the natural order is: ge(field_value, clause['value']

            # But!
            # Reversed operator order for contains (b in a)
            if isinstance(cval, list) or isinstance(fval, list):
                if clause['operator'] in ['one_of', 'matches']:
                    reversed_order = True
                    # But not in every case. (i.e. tags matches 'b')
                    # Here field_value is a list, because an annotation can
                    # have many tags.
                    if isinstance(field_value, list):
                        reversed_order = False

            if reversed_order:
                lval = cval
                rval = fval
            else:
                lval = fval
                rval = cval

            op = getattr(operator, self.operators[clause['operator']])
            return op(lval, rval)

    # match_policies
    def include_any(self, target):
        for clause in self.filter['clauses']:
            if self.evaluate_clause(clause, target):
                return True
        return False

    def include_all(self, target):
        for clause in self.filter['clauses']:
            if not self.evaluate_clause(clause, target):
                return False
        return True

    def exclude_all(self, target):
        for clause in self.filter['clauses']:
            if not self.evaluate_clause(clause, target):
                return True
        return False

    def exclude_any(self, target):
        for clause in self.filter['clauses']:
            if self.evaluate_clause(clause, target):
                return False
        return True

    def match(self, target, action=None):
        if not action or action == 'past' or action in self.filter['actions']:
            if len(self.filter['clauses']) > 0:
                return getattr(self, self.filter['match_policy'])(target)
            else:
                return True
        else:
            return False


class WebSocket(_WebSocket):
    # Class attributes
    reader = None
    instances = weakref.WeakSet()
    origins = []

    # Instance attributes
    client_id = None
    filter = None
    request = None
    query = None

    offsetFrom = 0
    received = 0

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('heartbeat_freq', 30.0)
        super(WebSocket, self).__init__(*args, **kwargs)
        self.request = get_current_request()

    def __new__(cls, *args, **kwargs):
        instance = super(WebSocket, cls).__new__(cls, *args, **kwargs)
        cls.instances.add(instance)
        return instance

    @classmethod
    def start_reader(cls, request):
        reader_id = 'stream-{}#ephemeral'.format(_random_id())
        cls.reader = request.get_queue_reader('annotations', reader_id)
        gevent.spawn(broadcast_from_queue, cls.reader, cls.instances)

    def opened(self):
        transaction.commit()  # Release the database transaction

        if self.reader is None:
            self.start_reader(self.request)

    def send_annotations(self):
        request = self.request
        user = get_user(request)
        annotations = Annotation.search_raw(query=self.query.query, user=user)
        self.received = len(annotations)

        packet = _annotation_packet(annotations, 'past')
        data = json.dumps(packet)
        self.send(data)

    def _expand_clauses(self, payload):
        for clause in payload['clauses']:
            if clause['field'] == '/uri':
                self._expand_uris(clause)

    def _expand_uris(self, clause):
        uris = clause['value']
        if not isinstance(uris, list):
            uris = [uris]

        if len(uris) < 1:
            return

        available_uris = set(uris)
        for uri in uris:
            doc = document.Document.get_by_uri(uri)
            # get_by_uri() returns an empty list when no document is found
            if isinstance(doc, list):
                return
            for eq_uri in doc.uris():
                available_uris.add(eq_uri)

        clause['value'] = list(available_uris)

    def received_message(self, msg):
        transaction.begin()
        try:
            data = json.loads(msg.data)
            msg_type = data.get('messageType', 'filter')

            if msg_type == 'filter':
                payload = data['filter']
                self.offsetFrom = 0

                # Let's try to validate the schema
                validate(payload, filter_schema)

                # Add backend expands for clauses
                self._expand_clauses(payload)

                self.filter = FilterHandler(payload)
                self.query = FilterToElasticFilter(payload, self.request)
                self.offsetFrom = 0
            elif msg_type == 'more_hits':
                if self.query is not None:
                    more_hits = data.get('moreHits', 10)

                    self.query.query['from'] = self.offsetFrom
                    self.query.query['size'] = more_hits
                    self.send_annotations()
                    self.offsetFrom += self.received
            elif msg_type == 'client_id':
                self.client_id = data.get('value')
        except:
            log.exception("Parsing filter: %s", msg)
            transaction.abort()
            self.close()
        else:
            transaction.commit()


def _annotation_packet(annotations, action):
    """
    Generate a packet suitable for sending down the websocket that represents
    the specified action applied to the passed annotations.
    """
    return {
        'payload': annotations,
        'type': 'annotation-notification',
        'options': {'action': action},
    }


def broadcast_from_queue(queue, sockets):
    """
    Pulls messages from a passed queue object, and handles dispatching them to
    appropriate active sessions.
    """
    for message in queue:
        data_in = json.loads(message.body)
        action = data_in['action']
        annotation = Annotation(**data_in['annotation'])
        payload = _annotation_packet([annotation], action)
        data_out = json.dumps(payload)
        for socket in list(sockets):
            if should_send_event(socket, annotation, data_in):
                socket.send(data_out)
        message.fin()


def should_send_event(socket, annotation, event_data):
    """
    Inspects the passed annotation and action and decides whether or not
    the underlying session should receive the event. If it should, the
    action is wrapped up in a websocket packet and sent to the client.
    """
    if socket.terminated:
        return False

    if event_data['action'] == 'read':
        return False

    if event_data['src_client_id'] == socket.client_id:
        return False

    if not socket.request.has_permission('read', annotation):
        return False

    # We don't send anything until we have received a filter from the client
    if socket.filter is None:
        return False

    if not socket.filter.match(annotation, event_data['action']):
        return False

    return True


def _random_id():
    """Generate a short random string"""
    data = struct.pack('Q', random.getrandbits(64))
    return base64.urlsafe_b64encode(data).strip(b'=')


def websocket(request):
    # WebSockets can be opened across origins and send cookies. To prevent
    # scripts on other sites from using this socket, ensure that the Origin
    # header (if present) matches the request host URL or is whitelisted.
    origin = request.headers.get('Origin')
    allowed = getattr(request.registry, 'websocket_origins', [])
    if origin is not None:
        if origin != request.host_url and origin not in allowed:
            return HTTPForbidden()
    return request.get_response(request.registry.websocket)


def bad_handshake(exc, request):
    log.error("streamer websocket handshake error: %s", exc)
    return HTTPBadRequest()


def includeme(config):
    origins = aslist(config.registry.settings.get('origins', ''))
    config.registry.websocket = WebSocketWSGIApplication(handler_cls=WebSocket)
    config.registry.websocket_origins = origins
    config.add_route('ws', 'ws')
    config.add_view(websocket, route_name='ws')
    config.add_view(bad_handshake, context=HandshakeError)
    config.scan(__name__)
