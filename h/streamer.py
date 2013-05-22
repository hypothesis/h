import json
import threading
import traceback

import requests
from urlparse import urlparse, urlunparse

import BeautifulSoup
import re
import Queue

from pyramid_sockjs.session import Session
from jsonschema import validate
from jsonpointer import resolve_pointer

from dateutil.tz import tzutc
from dateutil.parser import parse
from datetime import datetime, timedelta

from annotator import authz
from h import interfaces

import logging
log = logging.getLogger(__name__)

class UrlAnalyzer(dict):
    def urlEncodeNonAscii(self, b):
        return re.sub('[\x80-\xFF]', lambda c: '%%%02x' % ord(c.group(0)), b)

    def iriToUri(self, iri):
        parts= urlparse(iri)
        return urlunparse(
            part.encode('idna') if parti==1 else self.urlEncodeNonAscii(part.encode('utf-8'))
            for parti, part in enumerate(parts)
        )

    def _url_values(self, uri = None):
        if not uri: uri = self['uri']
        # Getting the title of the uri.
        try:
            r = requests.get(self.iriToUri(uri), verify=False)
            soup = BeautifulSoup.BeautifulSoup(r.content)
            title = soup.title.string if soup.title else uri

            # Favicon
            favlink = soup.find("link", rel="shortcut icon")
        except:
            log.info('Error opening url')
            log.info(traceback.format_exc())
            title = uri
            favlink = None

        # Getting the domain from the uri, and the same url magic for the
        # domain title.
        parsed_uri = urlparse(uri)
        domain = '{}://{}/'.format(parsed_uri[0], parsed_uri[1])
        domain_stripped = parsed_uri[1]
        if parsed_uri[1].lower().startswith('www.'):
            domain_stripped = domain_stripped[4:]

        # Check for local/global link.
        if favlink:
            href = favlink['href']
            if href.startswith('//') or href.startswith('http'):
                icon_link = href
            else:
                icon_link = domain + href
        else:
            icon_link = ''

        return {
            'title': title,
            'source': domain,
            'source_stripped': domain_stripped,
            'favicon_link': icon_link
        }

filter_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "optional": True},
        "match_policy": {
            "type": "string",
            "enum": ["include_any", "include_all", "exclude_any", "exclude_all"]
        },
        "actions": {
            "create": {"type": "boolean", "default":  True},
            "edit": {"type": "boolean", "default":  True},
            "delete": {"type": "boolean", "default":  True},
        },
        "clauses": {
            "type": "array",
            "items": {
                "field": {"type": "string", "format": "json-pointer"},
                "operator": {
                    "type": "string",
                    "enum": ["equals", "matches", "lt", "le", "gt", "ge", "one_of","first_of"]
                },
                "value": "object"
            }
        },
        "past_data": {
            "load_past": {
                "type": "string",
                "enum": ["time", "hits", "none"]
            },
            "go_back": {"type": "minutes", "default": 5},
            "hits": {"type": "number", "default": 100}
        }
    },
    "required": ["match_policy", "clauses", "actions"]
}


class FilterHandler(object):
    def __init__(self, filter_json):
        self.filter = filter_json

    def _userName(self, user):
        if not user or user == '': return 'Annotation deleted.'
        else: return user.split(':')[1].split('@')[0]

    #operators
    def equals(self, a, b): return a == b
    def matches(self, a, b): return a.find(b) > -1
    def lt(self, a, b): return a < b
    def le(self, a, b): return a <= b
    def gt(self, a, b): return a > b
    def ge(self, a, b): return a >= b
    def one_of(self, a, b): return a in b
    def first_of(self, a, b): return a[0] == b

    def evaluate_clause(self, clause, target):
        field_value = resolve_pointer(target, clause['field'], None)
        if clause['field'] == '/user':
            field_value = self._userName(field_value)
        if field_value is None:
            return False
        else: return getattr(self, clause['operator'])(field_value, clause['value'])
    
    #match_policies
    def include_any(self, target):
        for clause in self.filter['clauses']:
            if self.evaluate_clause(clause, target): return True
        return False

    def include_all(self, target):
        for clause in self.filter['clauses']:
            if not self.evaluate_clause(clause, target): return False
        return True

    def exclude_all(self, target):
        for clause in self.filter['clauses']:
            if not self.evaluate_clause(clause, target): return True
        return False

    def exclude_any(self, target):
        for clause in self.filter['clauses']:
            if self.evaluate_clause(clause, target): return False
        return True

    def match(self, target, action=None):
        if not action or action == 'past' or self.filter['actions'][action]:
            if len(self.filter['clauses']) > 0:
                return getattr(self, self.filter['match_policy'])(target)
            else: return True
        else: return False


class StreamerSession(Session):
    connections = set()

    def on_open(self):
        self.filter = {}
        self.connections.add(self)

    def on_message(self, msg):
        try:
            log.info(msg)
            payload = json.loads(msg)
            #Let's try to validate the schema
            validate(payload, filter_schema)
            self.filter = FilterHandler(payload)

            #If past is given, send the annotations back.
            if "past_data" in payload and payload["past_data"] != "none":
                request = self.request
                registry = request.registry
                store = registry.queryUtility(interfaces.IStoreClass)(request)
                annotations = store.search()

                url_analyzer = UrlAnalyzer()
                to_send = []
                if payload["past_data"]["load_past"] == "time":
                    now = datetime.utcnow().replace(tzinfo=tzutc())
                    past = now - timedelta(seconds=60 * payload['past_data']['go_back'])
                    for annotation in annotations:
                        created = parse(annotation['created'])
                        if created >= past and self.filter.match(annotation):
                            annotation.update(url_analyzer._url_values(annotation['uri']))
                            to_send = [annotation] + to_send
                elif payload["past_data"]["load_past"] == "hits":
                    sent_hits = 0
                    for annotation in annotations:
                        if self.filter.match(annotation):
                            annotation.update(url_analyzer._url_values(annotation['uri']))
                            to_send = [annotation] + to_send
                            sent_hits += 1
                        if sent_hits >= payload["past_data"]["hits"]:
                            break

                #Finally send filtered annotations
                if len(to_send) > 0:
                    self.send([to_send, 'past'])
        except:
            log.info(traceback.format_exc())
            log.info('Failed to parse filter:' + str(msg))
            self.close()

    def on_close(self):
        log.info('closing ' + str(self))
        self.connections.remove(self)

q = Queue.Queue()


def init_streamer():
    t = threading.Thread(target=process_filters)
    t.daemon = True
    t.start()


def process_filters():
    url_analyzer = UrlAnalyzer()
    while True:
        (annotation, action) = q.get(True)
        annotation.update(url_analyzer._url_values(annotation['uri']))
        after_action(annotation, action)
        q.task_done()


def after_action(annotation, action):
    if not authz.authorize(annotation, 'read'): return

    for connection in StreamerSession.connections:
        try:
            if connection.filter.match(annotation, action):
                connection.send([annotation, action])
        except:
            log.info(traceback.format_exc())
            log.info('Filter error!')


def after_save(annotation):
    q.put((annotation, 'create'))


def after_update(annotation):
    q.put((annotation, 'update'))


def after_delete(annotation):
    q.put((annotation, 'delete'))


def includeme(config): pass
