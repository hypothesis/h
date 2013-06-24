import json
import traceback

import requests
from urlparse import urlparse, urlunparse

import BeautifulSoup
import re

from pyramid.events import subscriber
from pyramid_sockjs.session import Session
from jsonschema import validate
from jsonpointer import resolve_pointer

from dateutil.tz import tzutc
from dateutil.parser import parse
from datetime import datetime, timedelta

from annotator import authz
from h import events, interfaces

import logging
log = logging.getLogger(__name__)


def check_favicon(icon_link, parsed_uri, domain):
    if icon_link:
        if icon_link.startswith('http'):
            icon_link = icon_link
        elif icon_link.startswith('//'):
            icon_link= parsed_uri[0] + "://" + icon_link[2:]
        else:
            icon_link = domain + icon_link
        #Check if the icon_link url really exists
        try:
            r2 = requests.head(icon_link)
            if r2.status_code != 200:
                icon_link = ''
        except:
            log.info(traceback.format_exc())
    else:
        icon_link = ''

    return icon_link

def url_values_from_document(annotation):
    title = annotation['uri']
    icon_link = ""

    parsed_uri = urlparse(annotation['uri'])
    domain = '{}://{}/'.format(parsed_uri[0], parsed_uri[1])
    domain_stripped = parsed_uri[1]
    if parsed_uri[1].lower().startswith('www.'):
        domain_stripped = domain_stripped[4:]

    if 'document' in annotation:
        if 'title' in annotation['document']:
            title = annotation['document']['title']

        if 'favicon' in annotation['document']:
            icon_link = annotation['document']['favicon']

        icon_link = check_favicon(icon_link, parsed_uri, domain)
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
                    "enum": ["equals", "matches", "lt", "le", "gt", "ge", "one_of", "first_of"]
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
            "hits": {"type": "number", "default": 100},
        }
    },
    "required": ["match_policy", "clauses", "actions"]
}


class FilterToElasticFilter(object):
    def __init__(self, filter_json):
        self.filter = filter_json
        self.query = {
            "query": {
                "bool": {
                    "minimum_number_should_match": 1}}}

        if len(self.filter['clauses']):
            clauses = self.convert_clauses(self.filter['clauses'])
            #apply match policy
            getattr(self, self.filter['match_policy'])(self.query['query']['bool'], clauses)
        else:
            self.query['query'] = {"match_all": {}}

        if self.filter['past_data']['load_past'] == 'time':
            now = datetime.utcnow().replace(tzinfo=tzutc())
            past = now - timedelta(seconds=60 * self.filter['past_data']['go_back'])
            converted = past.strftime("%Y-%m-%dT%H:%M:%S")
            self.query['filter'] = {"range": {"created": {"gte": converted}}}
        elif self.filter['past_data']['load_past'] == 'hits':
            self.query['filter'] = {"limit": {"value": self.filter['past_data']['hits']}}

    def equals(self, field, value):
        return {"term": {field: value}}

    def one_of(self, field, value):
        return {"term": {field: value}}

    def first_of(self, field, value):
        #TODO: proper implementation
        return {"term": {field: value}}

    def matches(self, field, value):
        return {"text": {field: value}}

    def lt(self, field, value):
        return {"range": {field: {"lt": value}}}

    def le(self, field, value):
        return {"range": {field: {"lte": value}}}

    def gt(self, field, value):
        return {"range": {field: {"gt": value}}}

    def ge(self, field, value):
        return {"range": {field: {"gte": value}}}

    def convert_clauses(self, clauses):
        new_clauses = []
        for clause in clauses:
            field = clause['field'][1:].replace('/', '.')
            new_clause = getattr(self, clause['operator'])(field, clause['value'])
            new_clauses.append(new_clause)
        return new_clauses

    def _policy(self, operator, target, clauses):
        target[operator] = []
        for clause in clauses:
            target[operator].append(clause)

    def include_any(self, target, clauses):
        self._policy('should', target, clauses)

    def include_all(self, target, clauses):
        self._policy('must', target, clauses)

    def exclude_any(self, target, clauses):
        self._policy('must_not', target, clauses)

    def exclude_any(self, target, clauses):
        target['must_not'] = {"bool": {}}
        self._policy('must', target['must_not']['bool'], clauses)


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
            payload = json.loads(msg)
            #Let's try to validate the schema
            validate(payload, filter_schema)
            self.filter = FilterHandler(payload)

            #If past is given, send the annotations back.
            if "past_data" in payload and payload["past_data"] != "none":
                query = FilterToElasticFilter(payload)
                request = self.request
                registry = request.registry
                store = registry.queryUtility(interfaces.IStoreClass)(request)
                #if payload["past_data"]["load_past"] == "replies":
                #    annotations = store.search(references=payload["past_data"]['id_for_reply'])
                #else:
                #    annotations = store.search()
                log.info('----------------------------------------')
                log.info(query.query)
                log.info('----------------------------------------')
                annotations = store.search_raw(json.dumps(query.query))
                #log.info(str(test))
                #log.info('----------------------------------------')

                log.info('----------------------------------------')
                log.info(type(annotations))
                log.info(len(annotations))
                log.info('----------------------------------------')


                for annotation in annotations:
                    annotation.update(url_values_from_document(annotation))


                #if payload["past_data"]["load_past"] == "time":
                #    now = datetime.utcnow().replace(tzinfo=tzutc())
                #    past = now - timedelta(seconds=60 * payload['past_data']['go_back'])
                #    for annotation in annotations:
                #        created = parse(annotation['created'])
                #        if created >= past and self.filter.match(annotation):
                #            annotation.update(UrlAnalyzer.url_values_from_document(annotation))
                #            to_send = [annotation] + to_send
                #elif payload["past_data"]["load_past"] == "hits":
                #    sent_hits = 0
                #    for annotation in annotations:
                #        if self.filter.match(annotation):
                #            annotation.update(UrlAnalyzer.url_values_from_document(annotation))
                #            to_send = [annotation] + to_send
                #            sent_hits += 1
                #        if sent_hits >= payload["past_data"]["hits"]:
                #            break
                #elif payload["past_data"]["load_past"] == "replies":
                #    sent_hits = 0
                #    for annotation in annotations:
                #        to_send = [annotation] + to_send
                #        sent_hits += 1

                #Finally send filtered annotations
                if len(annotations) > 0:
                    log.info('sending')
                    self.send([annotations, 'past'])
        except:
            log.info(traceback.format_exc())
            log.info('Failed to parse filter:' + str(msg))
            self.close()

    def on_close(self):
        log.info('closing ' + str(self))
        self.connections.remove(self)


@subscriber(events.AnnotatorStoreEvent)
def after_action(event):
    action = event.action
    annotation = event.annotation

    if action != 'create':
        if not authz.authorize(annotation, action):
            return

    for connection in StreamerSession.connections:
        try:
            if connection.filter.match(annotation, action):
                annotation.update(url_values_from_document(annotation))
                connection.send([annotation, action])
        except:
            log.info(traceback.format_exc())
            log.info('Filter error!')


def includeme(config):
    config.include('pyramid_sockjs')
    config.add_sockjs_route(prefix='__streamer__', session=StreamerSession)
    config.scan(__name__)
