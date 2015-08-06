# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from pyramid import security

from annotator import annotation
from annotator import document


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
                        principal = security.Everyone
                    elif role == 'group:__authenticated__':
                        principal = security.Authenticated
                    elif role == 'group:__consumer__':
                        raise NotImplementedError("API consumer groups")
                    else:
                        principal = role
                else:
                    principal = role

                # Append the converted rule tuple to the ACL
                rule = (security.Allow, principal, action)
                acl.append(rule)

        if acl:
            return acl
        else:
            # If there is no acl, it's an admin party!
            return [(security.Allow,
                     security.Everyone,
                     security.ALL_PERMISSIONS)]

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
            'index_analyzer': 'uri',
            'search_analyzer': 'uri',
            'fields': {
                'parts': {
                    'type': 'string',
                    'index_analyzer': 'uri_parts',
                    'search_analyzer': 'uri_parts',
                },
            },
        },
        'user': {'type': 'string', 'index': 'analyzed', 'analyzer': 'user'},
        'consumer': {'type': 'string'},
        'target': {
            'properties': {
                'source': {
                    'type': 'string',
                    'index_analyzer': 'uri',
                    'search_analyzer': 'uri',
                    'copy_to': ['uri'],
                },
                # We store the 'source_normalized' unanalyzed and only do term
                # filters against this field.
                'source_normalized': {
                    'type': 'string',
                    'index': 'not_analyzed',
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
        'char_filter': {
            'strip_scheme': {
                'type': 'pattern_replace',
                'pattern': r'^(?:[A-Za-z][A-Za-z.+-]+:)?/{0,3}',
                'replacement': '',
            },
        },
        'filter': {
            'path_url': {
                'type': 'pattern_capture',
                'preserve_original': 'false',
                'patterns': [
                    r'([0-9.\-A-Za-z]+(?::\d+)?(?:/[^?#]*))?',
                ],
            },
            'rstrip_slash': {
                'type': 'pattern_replace',
                'pattern': '/$',
                'replacement': '',
            },
            'user': {
                'type': 'pattern_capture',
                'preserve_original': 'true',
                'patterns': ['^acct:((.+)@.*)$']
            }
        },
        'tokenizer': {
            'uri_part': {
                'type': 'pattern',
                'pattern': r'[#+/:=?.-]|(?:%2[3BF])|(?:%3[ADF])',
            }
        },
        'analyzer': {
            'thread': {
                'tokenizer': 'path_hierarchy'
            },
            'uri': {
                'tokenizer': 'keyword',
                'char_filter': ['strip_scheme'],
                'filter': ['path_url', 'rstrip_slash', 'lowercase'],
            },
            'uri_parts': {
                'tokenizer': 'uri_part',
                'filter': ['unique'],
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
