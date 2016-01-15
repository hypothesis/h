# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from annotator import annotation
from annotator import document

from h._compat import text_type


class Annotation(annotation.Annotation):
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
        'target': {
            'properties': {
                'source': {
                    'type': 'string',
                    'index_analyzer': 'uri',
                    'search_analyzer': 'uri',
                    'copy_to': ['uri'],
                },
                # We store the 'scope' unanalyzed and only do term filters
                # against this field.
                'scope': {
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
        },
        'group': {
            'type': 'string',
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

    @property
    def uri(self):
        """Return this annotation's URI or an empty string.

        The uri is escaped and safe to be rendered.

        The uri is a Markup object so it won't be double-escaped.

        """
        uri_ = self.get("uri")
        if uri_:
            # Convert non-string URIs into strings.
            # If the URI is already a unicode string this will do nothing.
            # We're assuming that URI cannot be a byte string.
            return text_type(uri_)
        else:
            return ""

    @property
    def parent(self):
        """
        Return the thread parent of this annotation, if it exists.
        """
        if 'references' not in self:
            return None
        if not isinstance(self['references'], list):
            return None
        if not self['references']:
            return None
        return Annotation.fetch(self['references'][-1])

    @property
    def target_links(self):
        """A list of the URLs to this annotation's targets."""
        links = []
        targets = self.get("target")
        if isinstance(targets, list):
            for target in targets:
                if not isinstance(target, dict):
                    continue
                source = target.get("source")
                if source is None:
                    continue
                links.append(source)
        return links

    @property
    def document(self):
        return self.get("document", {})


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
