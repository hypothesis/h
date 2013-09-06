try:
    import simplejson as json
except ImportError:
    import json

import operator
import traceback

from datetime import datetime, timedelta
from urlparse import urlparse

import requests
import transaction

from dateutil.tz import tzutc

from jsonpointer import resolve_pointer
from jsonschema import validate

from pyramid.events import subscriber
from pyramid.security import has_permission

from pyramid_sockjs.session import Session

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
        # Check if the icon_link url really exists
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
            "update": {"type": "boolean", "default":  True},
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
                "value": "object",
                "case_sensitive": {"type": "boolean", "default": True}
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
            # apply match policy
            getattr(self, self.filter['match_policy'])(self.query['query']['bool'], clauses)
        else:
            self.query['query'] = {"match_all": {}}

        if self.filter['past_data']['load_past'] == 'time':
            now = datetime.utcnow().replace(tzinfo=tzutc())
            past = now - timedelta(seconds=60 * self.filter['past_data']['go_back'])
            converted = past.strftime("%Y-%m-%dT%H:%M:%S")
            self.query['filter'] = {"range": {"created": {"gte": converted}}}
        elif self.filter['past_data']['load_past'] == 'hits':
            self.query['size'] = self.filter['past_data']['hits']

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


def first_of(a, b): return a[0] == b
setattr(operator, 'first_of', first_of)


class FilterHandler(object):
    def __init__(self, filter_json):
        self.filter = filter_json

    # operators
    operators = {
        "equals": 'eq', "matches": 'contains', "lt": 'lt', "le": 'le', "gt": 'gt',
        "ge": 'ge', "one_of": 'contains', "first_of": 'first_of'
    }

    def evaluate_clause(self, clause, target):
        field_value = resolve_pointer(target, clause['field'], None)
        if field_value is None:
            return False
        else:
            if not clause['case_sensitive']:
                if type(clause['value']) is list:
                    cval = [x.lower() for x in clause['value']]
                else:
                    cval = clause['value'].lower()
                if type(field_value) is list:
                    fval = [x.lower() for x in field_value]
                else:
                    fval = field_value.lower()
            else:
                cval = clause['value']
                fval = field_value

            reversed = False
            # Determining operator order
            # Normal order: field_value, clause['value'] (i.e. condition created > 2000.01.01)
            # Here clause['value'] = '2001.01.01'. The field_value is target['created']
            # So the natural order is: ge(field_value, clause['value']

            # But!
            # Reversed operator order for contains (b in a)
            if clause['operator'] == 'one_of' or clause['operator'] == 'matches':
                reversed = True
                # But not in every case. (i.e. tags matches 'b')
                # Here field_value is a list, because an annotation can have many tags
                # And clause['value'] is 'b'
                if type(field_value) is list:
                    reversed = False

            if reversed:
                return getattr(operator, self.operators[clause['operator']])(cval, fval)
            else:
                return getattr(operator, self.operators[clause['operator']])(fval, cval)

    # match_policies
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
        if not action or action == 'past' or action in self.filter['actions']:
            if len(self.filter['clauses']) > 0:
                return getattr(self, self.filter['match_policy'])(target)
            else: return True
        else: return False


class StreamerSession(Session):
    def on_open(self):
        self.filter = {}
        transaction.commit()  # Release the database transaction

    def on_message(self, msg):
        transaction.begin()
        try:
            struct = json.loads(msg)
            payload = struct['filter']

            # Let's try to validate the schema
            validate(payload, filter_schema)
            self.filter = FilterHandler(payload)
            self.clientID = struct['clientID'] if 'clientID' in struct else ''

            # If past is given, send the annotations back.
            if "past_data" in payload and payload["past_data"]["load_past"] != "none":
                query = FilterToElasticFilter(payload)
                request = self.request
                registry = request.registry
                store = registry.queryUtility(interfaces.IStoreClass)(request)
                annotations = store.search_raw(query.query)

                send_annotations = []
                for annotation in annotations:
                    try:
                        annotation.update(url_values_from_document(annotation))
                        if 'references' in annotation:
                            parent = store.read(annotation['references'][-1])
                            if 'text' in parent:
                                annotation['quote'] = parent['text']
                        send_annotations.append(annotation)
                    except:
                        log.info(traceback.format_exc())
                        log.info("Error while updating the annotation's properties:" + str(annotation))

                # Finally send filtered annotations
                if len(annotations) > 0:
                    packet = {
                        'payload': send_annotations,
                        'type': 'annotation-notification',
                        'options': {
                            'action': 'past',
                            'clientID': self.clientID
                        }
                    }
                    self.send(packet)
        except:
            log.info(traceback.format_exc())
            log.info('Failed to parse filter:' + str(msg))
            transaction.abort()
            self.close()
        else:
            transaction.commit()

@subscriber(events.AnnotationEvent)
def after_action(event):
    try:
        request = event.request
        action = event.action
        if action == 'read':
            return

        annotation = event.annotation

        annotation.update(url_values_from_document(annotation))

        manager = request.get_sockjs_manager()
        for session in manager.active_sessions():
            try:
                if not has_permission('read', annotation, session.request):
                    continue

                registry = session.request.registry
                store = registry.queryUtility(interfaces.IStoreClass)(session.request)
                if 'references' in annotation:
                    parent = store.read(annotation['references'][-1])
                    if 'text' in parent:
                        annotation['quote'] = parent['text']

                if not session.filter.match(annotation, action):
                    continue

                client_id = request.headers['X-Client-Id'] if 'X-Client-Id' in request.headers else ''
                packet = {
                    'payload': [annotation],
                    'type': 'annotation-notification',
                    'options': {
                        'action': action,
                        'clientID': client_id
                    }
                }
                session.send(packet)
            except:
                log.info(traceback.format_exc())
                log.info('An error occured during the match checking or the annotation sending phase. ')
                log.info(str(annotation))
                log.info(str(session.filter))
    except:
        log.info(traceback.format_exc())
        log.info('Unexpected error occurred in after_action(): ' + str(event))


def includeme(config):
    config.include('pyramid_sockjs')
    config.add_sockjs_route(prefix='__streamer__', session=StreamerSession)
    config.scan(__name__)
