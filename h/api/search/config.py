# -*- coding: utf-8 -*-

"""
Index mappings and analysis settings for Elasticsearch, and associated tools.

This module contains the index mappings and analysis settings for data indexed
into Elasticsearch. It also contains some helper functions to create and update
these settings in an Elasticsearch instance.
"""

from __future__ import unicode_literals
import logging

import elasticsearch

log = logging.getLogger(__name__)

ANNOTATION_MAPPING = {
    '_id': {'path': 'id'},
    '_source': {'excludes': ['id']},
    'analyzer': 'keyword',
    'properties': {
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
}

ANNOTATION_ANALYSIS = {
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

DOCUMENT_MAPPING = {
    '_id': {'path': 'id'},
    '_source': {'excludes': ['id']},
    'analyzer': 'keyword',
    'date_detection': False,
    'properties': {
        'id': {'type': 'string', 'index': 'no'},
        'annotator_schema_version': {'type': 'string'},
        'created': {'type': 'date'},
        'updated': {'type': 'date'},
        'title': {'type': 'string', 'analyzer': 'standard'},
        'link': {
            'type': 'nested',
            'properties': {
                'type': {'type': 'string'},
                'href': {'type': 'string'},
            }
        },
        'dc': {
            'type': 'nested',
            'properties': {
                # by default elastic search will try to parse this as
                # a date but unfortunately the data that is in the wild
                # may not be parsable by ES which throws an exception
                'date': {'type': 'string'}
            }
        }
    }
}

DOCUMENT_ANALYSIS = {}


def configure_index(client, index=None):
    """Configure the elasticsearch index."""

    if index is None:
        index = client.index

    # Ensure the ICU analysis plugin is installed
    _ensure_icu_plugin(client.conn)

    # Construct desired mappings and analysis settings
    mappings = {}
    analysis = {}
    _append_config(mappings,
                   analysis,
                   client.t.annotation,
                   ANNOTATION_MAPPING,
                   ANNOTATION_ANALYSIS)
    _append_config(mappings,
                   analysis,
                   client.t.document,
                   DOCUMENT_MAPPING,
                   DOCUMENT_ANALYSIS)

    # Try to create the index with the correct settings. This will not fail if
    # the index already exists.
    _create_index(client.conn, index, {
        'mappings': mappings,
        'settings': {'analysis': analysis},
    })

    # For indices we didn't just create: try and update the analysis and
    # mappings to their current values. May throw an exception if elasticsearch
    # throws a MergeMappingException indicating that the index cannot be
    # updated without reindexing.
    _update_index_analysis(client.conn, index, analysis)
    _update_index_mappings(client.conn, index, mappings)


def _ensure_icu_plugin(conn):
    """Ensure that the ICU analysis plugin is installed for ES."""
    # Pylint issue #258: https://bitbucket.org/logilab/pylint/issue/258
    #
    # pylint: disable=unexpected-keyword-arg
    names = [x.strip() for x in conn.cat.plugins(h='component').split('\n')]
    if 'analysis-icu' not in names:
        message = ("The Elasticsearch ICU Analysis plugin is not installed. "
                   "Refer to "
                   "https://github.com/elastic/elasticsearch-analysis-icu "
                   "for installation instructions.")
        raise RuntimeError(message)


def _append_config(mappings, analysis, doc_type, type_mappings, type_analysis):
    """
    Append config for the named type to pre-existing config.

    This function takes a mappings dict and an analysis dict which may contain
    prior data, and attempts to update them with mappings and analysis settings
    for the named type.
    """
    mappings.update({doc_type: type_mappings})
    for section, items in type_analysis.items():
        existing_items = analysis.setdefault(section, {})
        for name in items:
            if name in existing_items:
                fmt = "Duplicate definition of 'index.analysis.{}.{}'."
                msg = fmt.format(section, name)
                raise RuntimeError(msg)
        existing_items.update(items)


def _create_index(conn, name, settings):
    """
    Create index with the specific name and settings.

    This function will ignore errors caused by the index already existing.
    """
    # Check if the index exists (perhaps as an alias) and if so, return.
    if conn.indices.exists(index=name):
        return

    # Otherwise, try to create the index
    conn.indices.create(name, body=settings)


def _update_index_analysis(conn, name, analysis):
    """Attempt to update the index analysis settings."""
    name = _resolve_alias(conn, name)
    settings = conn.indices.get_settings(index=name)
    existing = settings[name]['settings']['index'].get('analysis', {})
    if existing != analysis:
        try:
            conn.indices.close(index=name)
            conn.indices.put_settings(index=name, body={
                'analysis': analysis
            })
        finally:
            conn.indices.open(index=name)


def _update_index_mappings(conn, name, mappings):
    """Attempt to update the index mappings."""
    name = _resolve_alias(conn, name)
    try:
        for doc_type, body in mappings.items():
            conn.indices.put_mapping(index=name,
                                     doc_type=doc_type,
                                     body=body)
    except elasticsearch.exceptions.RequestError as e:
        if not e.error.startswith('MergeMappingException'):
            raise

        message = ("Elasticsearch index mapping cannot be automatically "
                   "updated! Please reindex it. You may find the `hypothesis "
                   "reindex` command helpful.")
        log.critical(message)
        raise RuntimeError(message)


def _resolve_alias(conn, name):
    """Resolve an alias into the underlying index name."""
    result = conn.indices.get_alias(index=name)

    # If there are no returned results, this isn't an alias
    if not result:
        return name

    # If there are multiple keys, we have to raise, because this code doesn't
    # support updating mappings for multiple indices.
    if len(result) > 1:
        raise RuntimeError("We don't support autocreating/updating aliases "
                           "that point to multiple indices at the moment!")

    return result.keys()[0]
