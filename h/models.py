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
                if role.startswith('group:'):
                    if role == 'group:__world__':
                        principal = Everyone
                    elif role == 'group:__authenticated__':
                        principal = Authenticated
                    elif role == 'group:__consumer__':
                        raise NotImplementedError("API consumer groups")
                    else:
                        principal = role
                elif role.startswith('acct:'):
                    principal = role
                else:
                    raise ValueError(
                        "Unrecognized role '%s' in annotation '%s'" %
                        (role, self.get('id'))
                    )

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
        'quote': {'type': 'string', 'analyzer': 'standard'},
        'tags': {'type': 'string', 'index': 'analyzed', 'analyzer': 'lower_keyword'},
        'text': {'type': 'string', 'analyzer': 'standard'},
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
                'id': {
                    'type': 'multi_field',
                    'path': 'just_name',
                    'fields': {
                        'id': {'type': 'string'},
                        'uri': {
                            'type': 'string',
                            'index_analyzer': 'uri_index',
                            'search_analyzer': 'uri_search'
                        },
                    },
                },
                'source': {
                    'type': 'multi_field',
                    'path': 'just_name',
                    'fields': {
                        'source': {'type': 'string'},
                        'uri': {
                            'type': 'string',
                            'index_analyzer': 'uri_index',
                            'search_analyzer': 'uri_search'
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
                            'type': 'multi_field',
                            'path': 'just_name',
                            'fields': {
                                'exact': {'type': 'string'},
                                'quote': {'type': 'string'},
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
            'properties': document.MAPPING
        },
        'thread': {
            'type': 'string',
            'analyzer': 'thread'
        }
    }
    __settings__ = {
        'analysis': {
            'filter': {
                'uri': {
                    'type': 'pattern_capture',
                    'preserve_original': 1,
                    'patterns': [
                        '([^\\/\\?\\#\\.]+)',
                        '([a-zA-Z0-9]+)(?:\\.([a-zA-Z0-9]+))*',
                        '([a-zA-Z0-9-]+)(?:\\.([a-zA-Z0-9-]+))*',
                    ]
                },
                'user': {
                    'type': 'pattern_capture',
                    'preserve_original': 1,
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
                }
            }
        }
    }

    @classmethod
    def update_settings(cls):
        # pylint: disable=no-member
        cls.es.conn.indices.close(index=cls.es.index)
        try:
            cls.es.conn.indices.put_settings(
                index=cls.es.index,
                body=getattr(cls, '__settings__', {})
            )
        finally:
            cls.es.conn.indices.open(index=cls.es.index)


class Document(document.Document):
    pass
