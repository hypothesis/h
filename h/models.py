# -*- coding: utf-8 -*-
from annotator import annotation, document
from pyramid.i18n import TranslationStringFactory
from pyramid.security import Allow, Authenticated, Everyone, ALL_PERMISSIONS

_ = TranslationStringFactory(__package__)


class Annotation(annotation.Annotation):
    def __acl__(self):
        acl = []
        # Convert annotator-store roles to pyramid principals
        for action, roles in self.get('permissions', {}).items():
            for role in roles:
                if role.startswith('system.'):
                    raise ValueError('{} is a reserved role.'.format(role))
                elif role.startswith('group:'):
                    if role == 'group:__world__':
                        principal = Everyone
                    elif role == 'group:__authenticated__':
                        principal = Authenticated
                    elif role == 'group:__consumer__':
                        raise NotImplementedError("API consumer groups")
                    else:
                        principal = role
                else:
                    principal = role

                # Append the converted rule tuple to the ACL
                rule = (Allow, principal, action)
                acl.append(rule)

        if acl:
            return acl
        else:
            # If there is no acl, it's an admin party!
            return [(Allow, Everyone, ALL_PERMISSIONS)]

    __mapping__ = {
        'annotator_schema_version': {'type': 'string'},
        'created': {'type': 'date'},
        'updated': {'type': 'date'},
        'quote': {'type': 'string', 'analyzer': 'uni_normalizer'},
        'tags': {'type': 'string', 'analyzer': 'uni_normalizer'},
        'text': {'type': 'string', 'analyzer': 'uni_normalizer'},
        'deleted': {'type': 'boolean'},
        'uri': {
            'type': 'string',
            'index_analyzer': 'uri_index',
            'search_analyzer': 'uri_search'
        },
        'user': {'type': 'string', 'index': 'analyzed', 'analyzer': 'user'},
        'consumer': {'type': 'string'},
        'target': {
            'properties': {
                'source': {
                    'path': 'just_name',
                    'type': 'string',
                    'fields': {
                        'uri': {
                            'type': 'string',
                            'index_analyzer': 'uri_index',
                            'search_analyzer': 'uri_search',
                        },
                    },
                },
                'selector': {
                    'properties': {
                        'type': {'type': 'string', 'index': 'no'},

                        # Annotator XPath+offset selector
                        'startContainer': {'type': 'string', 'index': 'no'},
                        'startOffset': {'type': 'long', 'index': 'no'},
                        'endContainer': {'type': 'string', 'index': 'no'},
                        'endOffset': {'type': 'long', 'index': 'no'},

                        # Open Annotation TextQuoteSelector
                        'exact': {
                            'path': 'just_name',
                            'type': 'string',
                            'fields': {
                                'quote': {
                                    'type': 'string',
                                    'analyzer': 'uni_normalizer',
                                },
                            },
                        },
                        'prefix': {'type': 'string'},
                        'suffix': {'type': 'string'},

                        # Open Annotation (Data|Text)PositionSelector
                        'start': {'type': 'long'},
                        'end':   {'type': 'long'},
                    }
                }
            }
        },
        'permissions': {
            'index_name': 'permission',
            'properties': {
                'read': {'type': 'string'},
                'update': {'type': 'string'},
                'delete': {'type': 'string'},
                'admin': {'type': 'string'}
            }
        },
        'references': {'type': 'string'},
        'document': {
            'enabled': False,  # indexed explicitly by the save function
        },
        'thread': {
            'type': 'string',
            'analyzer': 'thread'
        }
    }
    __analysis__ = {
        'filter': {
            'uri': {
                'type': 'pattern_capture',
                'preserve_original': '1',
                'patterns': [
                    '([^\\/\\?\\#\\.]+)',
                    '([a-zA-Z0-9]+)(?:\\.([a-zA-Z0-9]+))*',
                    '([a-zA-Z0-9-]+)(?:\\.([a-zA-Z0-9-]+))*',
                ]
            },
            'user': {
                'type': 'pattern_capture',
                'preserve_original': '1',
                'patterns': ['^acct:((.+)@.*)$']
            }
        },
        'analyzer': {
            'thread': {
                'tokenizer': 'path_hierarchy'
            },
            'lower_keyword': {
                'type': 'custom',
                'tokenizer': 'keyword',
                'filter': 'lowercase'
            },
            'uri_index': {
                'tokenizer': 'keyword',
                'filter': ['uri', 'unique']
            },
            'uri_search': {
                'tokenizer': 'keyword',
            },
            'user': {
                'tokenizer': 'keyword',
                'filter': ['user', 'lowercase']
            },
            'uni_normalizer': {
                'tokenizer': 'icu_tokenizer',
                'filter': ['icu_folding']
            }
        }
    }

    @classmethod
    def get_analysis(cls):
        return cls.__analysis__


class Document(document.Document):
    __analysis__ = {}

    @classmethod
    def get_analysis(cls):
        return cls.__analysis__

    @classmethod
    def get_mapping(cls):
        mapping = super(Document, cls).get_mapping()
        mapping['document']['date_detection'] = False
        return mapping


class Client(object):

    """A basic implementation of :class:`h.oauth.IClient`."""

    client_id = None
    client_secret = None

    def __init__(self, client_id):
        self.client_id = client_id
