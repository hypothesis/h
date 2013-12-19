try:
    import simplejson as json
except ImportError:
    import json

import operator
import traceback

from datetime import datetime, timedelta
from urlparse import urlparse

import transaction

from dateutil.tz import tzutc

from jsonpointer import resolve_pointer
from jsonschema import validate

from pyramid.events import subscriber
from pyramid.security import has_permission

from pyramid_sockjs.session import Session

from h import events, interfaces
from h.lib import get_session
import re

import logging
log = logging.getLogger(__name__)

from resources import Annotation
import mannord


def check_favicon(icon_link, parsed_uri, domain):
    if icon_link:
        if icon_link.startswith('http'):
            icon_link = icon_link
        elif icon_link.startswith('//'):
            icon_link= parsed_uri[0] + "://" + icon_link[2:]
        else:
            icon_link = domain + icon_link
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
        'uri': annotation['uri'],
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
                "case_sensitive": {"type": "boolean", "default": True},
                "es_query_string": {"type": "boolean", "default": False}
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
            "sort": [
                {"updated": {"order": "desc"}}
            ],
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

    @staticmethod
    def equals(field, value):
        return {"term": {field: value}}

    @staticmethod
    def one_of(field, value):
        return {"term": {field: value}}

    @staticmethod
    def first_of(field, value):
        return {"term": {field: value}}

    @staticmethod
    def match_of(field, value):
        #TODO: proper implementation
        return {"term": {field: value}}

    @staticmethod
    def matches(field, value):
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

    def convert_clauses(self, clauses):
        new_clauses = []
        for clause in clauses:
            field = clause['field'][1:].replace('/', '.')
            if not clause['case_sensitive']:
                if type(clause['value']) is list:
                    value = [x.lower() for x in clause['value']]
                else:
                    value = clause['value'].lower()
            else:
                value = clause['value']
            if clause["es_query_string"]:
                # Generate query_string query
                escaped_value = re.escape(value)
                new_clause = {
                    "query_string": {
                        "query": "*" + escaped_value + "*",
                        "fields": [field]
                    }
                }
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

    def exclude_any(self, target, clauses):
        target['must_not'] = {"bool": {}}
        self._policy('must', target['must_not']['bool'], clauses)


def first_of(a, b): return a[0] == b
setattr(operator, 'first_of', first_of)


def match_of(a, b):
    for subb in b:
        if subb in a:
            return True
    return False
setattr(operator, 'match_of', match_of)


class FilterHandler(object):
    def __init__(self, filter_json):
        self.filter = filter_json

    # operators
    operators = {
        "equals": 'eq', "matches": 'contains', "lt": 'lt', "le": 'le', "gt": 'gt',
        "ge": 'ge', "one_of": 'contains', "first_of": 'first_of', "match_of": 'match_of'
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
            if type(cval) is list or type(fval) is list:
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
    clientID = None
    filter = None

    def on_open(self):
        transaction.commit()  # Release the database transaction

    def send_annotations(self):
        request = self.request
        registry = request.registry
        store = registry.queryUtility(interfaces.IStoreClass)(request)
        annotations = store.search_raw(self.query.query)
        self.received = len(annotations)
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
        # Can send zero to indicate that no past data is matched
        if self.clientID is None:
            # Backwards-compatibility code
            packet = [send_annotations, 'past']
        else:
            packet = {
                'payload': send_annotations,
                'type': 'annotation-notification',
                'options': {
                    'action': 'past',
                    'clientID': self.clientID
                }
            }
        self.send(packet)

    def on_message(self, msg):
        transaction.begin()
        try:
            struct = json.loads(msg)
            self.clientID = struct['clientID'] if 'clientID' in struct else ''
            type = struct['messageType'] if 'messageType' in struct else 'filter'

            if type == 'filter':
                payload = struct['filter']
                self.offsetFrom = 0

                # Let's try to validate the schema
                validate(payload, filter_schema)
                self.filter = FilterHandler(payload)

                # If past is given, send the annotations back.
                if "past_data" in payload and payload["past_data"]["load_past"] != "none":
                    self.query = FilterToElasticFilter(payload)
                    if 'size' in self.query.query:
                        self.offsetFrom = int(self.query.query['size'])
                    self.send_annotations()
            elif type == 'more_hits':
                more_hits = int(struct['moreHits']) if 'moreHits' in struct else 50
                if 'size' in self.query.query:
                    self.query.query['from'] = self.offsetFrom
                    self.query.query['size'] = more_hits
                    self.send_annotations()
                    self.offsetFrom += self.received
        except:
            log.info(traceback.format_exc())
            log.info('Failed to parse filter:' + str(msg))
            transaction.abort()
            self.close()
        else:
            transaction.commit()


def get_annotation_resource(annot_id, request):
    """ Obtain annotation resource by annotation id."""
    registry = request.registry
    store = registry.queryUtility(interfaces.IStoreClass)(request)
    data = store.read(annot_id)

    annotation = Annotation(request)
    annotation.update(data)
    return annotation


def get_mannord_annotation_object(annot_id, request, session):
    """ The function returns a mannord annotation object with given id.
    If there is no record for annot_id then the function creates it.
    """
    annot_res = get_annotation_resource(annot_id, request)
    references = annot_res.get('references', [])
    # Id of parent annotation.
    parent_id = None if len(references) else references[-1]
    # Fetches action type
    action_type = None
    tags = annot_res.get('tags', [])
    if 'upvote' in tags:
        action_type = mannord.ACTION_UPVOTE
    elif 'downvote' in tags:
        action_type = mannord.ACTION_DOWNVOTE
    # Fetches author of the annotation.
    author = mannord.get_add_user(annot_res.get('user'), session)
    # Creates an annotation.
    annot = mannord.get_add_item(annot_res.get('uri'), annot_res.get('id'),
                                 author, session, parent_id=parent_id,
                                 action_type=action_type)
    return annot


def get_moderated_annotation(moderating_annotation, request, session):
    """ Method retruns a moderated annotation (mannord's object).
    Args:
        - moderating_annot is a resource annotation object that is a
        moderation action.
    """
    # Obtains a key of moderated annotation.
    references = moderating_annotation.get('references', [])
    if len(references) == 0:
        return None
    moderated_annot_id = references[-1]
    return get_mannord_annotation_object(moderated_annot_id, request, session)


@subscriber(events.AnnotationEvent)
def after_moderation_action(event):
    """ The function triggers mannords' moderation functions.
    """
    try:
        request = event.request
        action = event.action
        if action == 'read':
            return

        annotation = event.annotation
        session = get_session(request)

        # Checkes that moderating user is authenticated.
        if request.user is None:
            return

        # moderating_user is the user who have made moderation action.
        moderating_user = mannord.get_add_user(annotation['user'])

        tags = annotation.get('tags', [])
        moderated_annot = None
        # Checks whether the even is moderation action or not.
        if ('spam' in tags or 'ham' in tags or 'upvote' in tags or
             'downvote' in tags or 'delete_by_author' in tags):
            # The event is moderation action.
            moderated_annot = get_moderated_annotation(annotation, request, session)
            # Creates a mannord record about current moderating annotation.
            _ = get_mannord_annotation_object(annotation.get('id'), request, session)
            if moderated_annot is None:
                log.info('WARNING: Unable to fetch moderated annotation!')
                return
        else:
            # The event is not moderation action.
            return

        # Cheks for tags and calls appropriate mannord's moderation functions.
        if 'spam' in tags:
            # The annotation was flagged as spam.
            if moderated_annot.spam_flag_counter == 0:
                # The annotaion is being marked as a spam first time!
                # NOTE: this is a place to trigger an email sending to the author
                pass
            # Flag the anntaiton as spam.
            mannord.raise_spam_flag(moderated_annot, moderating_user, session)
        elif 'ham' in tags:
            # The annotation was flagged as not spam.
            mannord.raise_ham_flag(moderated_annot, moderating_user, session)
        elif 'upvote' in tags:
            if annotation.deleted:
                # Undo upvote
                mannord.undo_upvote(moderated_annot, moderating_user, session)
            else:
            # Upvote
                mannord.upvote(moderated_annot, moderating_user, session)
        elif 'downvote' in tags:
            if annotation.deleted:
                # Undo downvote
                mannord.undo_downvote(moderated_annot, moderating_user, session)
            else:
                # Downvote
                mannord.downvote(moderated_annot, moderating_user, session)
        elif 'delete_by_author' in tags:
            # Deletes the annotation, so that the author does not get repuatiton
            # damage.
            mannord.delete_spam_item_by_author(moderated_annot, session)
    except:
        log.info(traceback.format_exc())
        log.info('Unexpected error occurred in after_moderation_action(): ' + str(event))


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

                flt = session.filter
                if not (flt and flt.match(annotation, action)):
                    continue

                if session.clientID is None:
                    # Backwards-compatibility code
                    packet = [annotation, action]
                else:
                    packet = {
                        'payload': [annotation],
                        'type': 'annotation-notification',
                        'options': {
                            'action': action,
                            'clientID': request.headers.get('X-Client-Id'),
                        },
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
