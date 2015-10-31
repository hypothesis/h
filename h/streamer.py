# -*- coding: utf-8 -*-
import base64
import copy
import functools
import json
import logging
import operator
import random
import re
import struct
import unicodedata
import weakref

import gevent
from jsonpointer import resolve_pointer
from jsonschema import validate
from pyramid.config import aslist
from pyramid.events import ApplicationCreated
from pyramid.events import subscriber
from pyramid.httpexceptions import HTTPBadRequest, HTTPForbidden
from pyramid.threadlocal import get_current_request
from ws4py.exc import HandshakeError
from ws4py.websocket import WebSocket as _WebSocket
from ws4py.server.wsgiutils import WebSocketWSGIApplication

from h import queue
from h._compat import text_type
from h.api import nipsa
from h.api import uri
from h.api.search import query
from .models import Annotation, Group
import h.session

log = logging.getLogger(__name__)


def uni_fold(text):
    # Convert bytes to text
    if isinstance(text, bytes):
        text = text_type(text, "utf-8")

    # Do not touch other types
    if not isinstance(text, text_type):
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

        self.query["query"] = {
            "filtered": {
                "filter": {
                    "bool": {
                        "must": [
                            query.AuthFilter(request)({}),
                            nipsa.nipsa_filter(request.authenticated_userid),
                        ]
                    }
                },
                "query": self.query["query"]
            }
        }

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

            options = clause.get('options', {})
            es = options.get('es')
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


# NSQ message topics that the WebSocket server
# processes messages from
ANNOTATIONS_TOPIC = 'annotations'
USER_TOPIC = 'user'


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

    def send_annotations(self):
        user = self.user
        annotations = Annotation.search_raw(query=self.query.query)
        packet = _annotation_packet(annotations, 'past')
        data = json.dumps(packet)
        self.send(data)

    def _expand_clauses(self, payload):
        for clause in payload['clauses']:
            if clause['field'] == '/uri':
                self._expand_uris(clause)

    def _expand_uris(self, clause):
        uris = clause['value']
        expanded = set()

        if not isinstance(uris, list):
            uris = [uris]

        for item in uris:
            expanded.update(uri.expand(item))

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
                validate(payload, filter_schema)

                # Add backend expands for clauses
                self._expand_clauses(payload)

                self.filter = FilterHandler(payload)
                self.query = FilterToElasticFilter(payload, self.request)
            elif msg_type == 'client_id':
                self.client_id = data.get('value')
        except:
            # TODO: clean this up, catch specific errors, narrow the scope
            log.exception("Parsing filter: %s", msg)
            self.close()
            raise


def handle_annotation_event(message, socket):
    """
    Get message about annotation event `message` to be sent to `socket`.

    Inspects the embedded annotation event and decides whether or not the
    passed socket should receive notification of the event.

    Returns None if the socket should not receive any message about this
    annotation event, otherwise a dict containing information about the event.
    """
    action = message['action']
    annotation = Annotation(**message['annotation'])

    if action == 'read':
        return None

    if message['src_client_id'] == socket.client_id:
        return None

    if annotation.get('nipsa') and (
            socket.request.authenticated_userid != annotation.get('user', '')):
        return None

    if not _authorized_to_read(
            socket.request.effective_principals, annotation):
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


def _authorized_to_read(effective_principals, annotation):
    """Return True if effective_principals authorize reading annotation.

    Return True if the given effective_principals authorize the request that
    owns them to read the given annotation. False otherwise.

    If the annotation belongs to a private group, this will return False if the
    authenticated user isn't a member of that group.

    """
    if 'group:__world__' in annotation['permissions']['read']:
        return True
    for principal in effective_principals:
        if principal in annotation['permissions']['read']:
            return True
    return False


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
    sockets = list(WebSocket.instances)
    for socket in sockets:
        reply = handler(data, socket)
        if reply is None:
            continue
        if not socket.terminated:
            socket.send(json.dumps(reply))


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


def _random_id():
    """Generate a short random string"""
    data = struct.pack('Q', random.getrandbits(64))
    return base64.urlsafe_b64encode(data).strip(b'=')


@subscriber(ApplicationCreated)
def start_queue_processing(event):
    """
    Start some greenlets to process the incoming data from NSQ.

    This subscriber is called when the application is booted, and kicks off
    greenlets running `process_queue` for each NSQ topic we subscribe to. The
    function does not block.
    """
    def _loop(settings, topic, handler):
        while True:
            process_queue(settings, topic, handler)

    settings = event.app.registry.settings
    gevent.spawn(_loop, settings, ANNOTATIONS_TOPIC, handle_annotation_event)
    gevent.spawn(_loop, settings, USER_TOPIC, handle_user_event)


def websocket(request):
    # WebSockets can be opened across origins and send cookies. To prevent
    # scripts on other sites from using this socket, ensure that the Origin
    # header (if present) matches the request host URL or is whitelisted.
    origin = request.headers.get('Origin')
    allowed = aslist(request.registry.settings.get('origins', ''))
    if origin is not None:
        if origin != request.host_url and origin not in allowed:
            return HTTPForbidden()
    app = WebSocketWSGIApplication(handler_cls=WebSocket)
    return request.get_response(app)


def bad_handshake(exc, request):
    return HTTPBadRequest()


def includeme(config):
    config.add_route('ws', 'ws')
    config.add_view(websocket, route_name='ws')
    config.add_view(bad_handshake, context=HandshakeError)
    config.scan(__name__)
