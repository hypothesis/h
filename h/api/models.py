# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import cgi
from dateutil import parser
from annotator import annotation
from annotator import document
from annotator import es


class Annotation(annotation.Annotation):
    __mapping__ = {
        'annotator_schema_version': {'type': 'string'},
        'created': {'type': 'date'},
        'updated': {'type': 'date'},
        'quote': {'type': 'string', 'analyzer': 'uni_normalizer'},
        'tags': {'type': 'string', 'analyzer': 'uni_normalizer'},
        'text': {'type': 'string', 'analyzer': 'uni_normalizer'},
        'deleted': {'type': 'boolean'},
        'nipsa': {'type': 'boolean'},
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
    def title(self):
        """A title for this annotation."""
        document_ = self.get("document")
        if document_:
            return document_.get("title", "")
        else:
            return ""

    @property
    def description(self):
        """An HTML-formatted description of this annotation.

        The description contains the target text that the user selected to
        annotate, as a <blockquote>, and the body text of the annotation
        itself.

        """
        def get_selection():
            targets = self.get("target")
            if not isinstance(targets, list):
                return
            for target in targets:
                if not isinstance(target, dict):
                    continue
                selectors = target.get("selector")
                if not isinstance(selectors, list):
                    continue
                for selector in selectors:
                    if not isinstance(selector, dict):
                        continue
                    if "exact" in selector:
                        return selector["exact"]

        description = ""

        selection = get_selection()
        if selection:
            selection = cgi.escape(selection)
            description += u"&lt;blockquote&gt;{selection}&lt;/blockquote&gt;".format(
                selection=selection)

        text = self.get("text")
        if text:
            text = cgi.escape(text)
            description += u"{text}".format(text=text)

        return description

    @property
    def created_day_string(self):
        """A simple created day string for this annotation.

        Returns a day string like '2015-03-11' from the annotation's 'created'
        date.

        """
        return parser.parse(self["created"]).strftime("%Y-%m-%d")

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

    def percolate(self):
        # TODO: could pass 'id' instead of 'body' for efficiency.
        # Beware that after issuing a delete, this would cause an error.
        return self.es.conn.percolate(index=self.es.index,
                                      doc_type=self.__type__,
                                      body={'doc': self},
                                      percolate_format='ids')


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


class Percolator(es.Model):
    __type__ = '.percolator'
    __mapping__ = {
        '_ttl': {'enabled': True},
    }

    @classmethod
    def get_analysis(cls):
        return {}

    @classmethod
    def get_mapping(cls):
        return {
            cls.__type__: {
                '_id': {
                    'path': 'id',
                },
                '_ttl': {'enabled': True},
            }
        }
