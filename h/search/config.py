# -*- coding: utf-8 -*-

"""
Index mappings and analysis settings for Elasticsearch, and associated tools.

This module contains the index mappings and analysis settings for data indexed
into Elasticsearch. It also contains some helper functions to create and update
these settings in an Elasticsearch instance.
"""

from __future__ import unicode_literals

import binascii
import logging
import os

from elasticsearch.exceptions import NotFoundError, RequestError

log = logging.getLogger(__name__)

ANNOTATION_MAPPING = {
    '_source': {'excludes': ['_id']},
    'properties': {
        'annotator_schema_version': {'type': 'text'},
        'authority': {'type': 'keyword'},
        'created': {'type': 'date'},
        'updated': {'type': 'date'},
        'quote': {'type': 'text', 'analyzer': 'uni_normalizer'},
        'tags': {'type': 'text', 'analyzer': 'uni_normalizer'},
        'tags_raw': {'type': 'keyword'},
        'text': {'type': 'text', 'analyzer': 'uni_normalizer'},
        'deleted': {'type': 'boolean'},
        'uri': {
            'type': 'text',
            'analyzer': 'uri',
            'fields': {
                'parts': {
                    'type': 'text',
                    'analyzer': 'uri_parts',
                },
            },
        },
        'user': {'type': 'text', 'analyzer': 'user'},
        'user_raw': {'type': 'keyword'},
        'target': {
            'properties': {
                'source': {
                    'type': 'text',
                    'analyzer': 'uri',
                    'copy_to': ['uri'],
                },
                # We store the 'scope' unanalyzed and only do term filters
                # against this field.
                'scope': {
                    'type': 'keyword',
                },
                'selector': {
                    'properties': {
                        'type': {'type': 'keyword', 'index': False},

                        # Annotator XPath+offset selector
                        'startContainer': {'type': 'keyword', 'index': False},
                        'startOffset': {'type': 'long', 'index': False},
                        'endContainer': {'type': 'keyword', 'index': False},
                        'endOffset': {'type': 'long', 'index': False},

                        # Open Annotation TextQuoteSelector
                        'exact': {
                            'type': 'text',
                            'fields': {
                                'quote': {
                                    'type': 'text',
                                    'analyzer': 'uni_normalizer',
                                },
                            },
                        },
                        'prefix': {'type': 'text'},
                        'suffix': {'type': 'text'},

                        # Open Annotation (Data|Text)PositionSelector
                        'start': {'type': 'long'},
                        'end':   {'type': 'long'},
                    }
                }
            }
        },
        # FIXME: Remove once we've stopped indexing this field.
        'permissions': {
            'properties': {
                'read': {'type': 'text'},
                'update': {'type': 'text'},
                'delete': {'type': 'text'},
                'admin': {'type': 'text'}
            }
        },
        'shared': {'type': 'boolean'},
        'references': {'type': 'text'},
        'document': {
            'enabled': False,  # not indexed
        },
        'group': {
            'type': 'text',
        },
        'thread_ids': {
            'type': 'keyword',
        }
    }
}

ANALYSIS_SETTINGS = {
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


def init(client):
    """Initialise Elasticsearch, creating necessary indices and aliases."""
    # Ensure the ICU analysis plugin is installed
    _ensure_icu_plugin(client.conn)

    # If the index already exists (perhaps as an alias), we're done...
    if client.conn.indices.exists(index=client.index):
        return

    # Otherwise we create a new randomly-named index and alias it. This allows
    # us to straightforwardly reindex when we need to.
    concrete_index = configure_index(client)
    client.conn.indices.put_alias(index=concrete_index, name=client.index)


def configure_index(client):
    """Create a new randomly-named index and return its name."""
    index_name = client.index + '-' + _random_id()

    client.conn.indices.create(index_name, body={
        'mappings': {
            client.t.annotation: ANNOTATION_MAPPING,
        },
        'settings': {
            'analysis': ANALYSIS_SETTINGS,
        },
    })

    return index_name


def get_aliased_index(client):
    """
    Fetch the name of the underlying index.

    Returns ``None`` if the index is not aliased or does not exist.
    """
    try:
        result = client.conn.indices.get_alias(name=client.index)
    except NotFoundError:  # no alias with that name
        return None
    if len(result) > 1:
        raise RuntimeError("We don't support managing aliases that "
                           "point to multiple indices at the moment!")
    return list(result.keys())[0]


def update_aliased_index(client, new_target):
    """
    Update the alias to point to a new target index.

    Will raise `RuntimeError` if the index is not aliased or does not
    exist.
    """
    old_target = get_aliased_index(client)
    if old_target is None:
        raise RuntimeError("Cannot update aliased index for index that "
                           "is not already aliased.")

    client.conn.indices.update_aliases(body={
        'actions': [
            {'add': {'index': new_target, 'alias': client.index}},
            {'remove': {'index': old_target, 'alias': client.index}},
        ],
    })


def update_index_settings(client):
    """
    Update the index settings (analysis and mappings) to their current state.

    May raise if Elasticsearch throws a MergeMappingException indicating that
    the index cannot be updated without reindexing.
    """
    index = get_aliased_index(client)
    _update_index_analysis(client.conn, index, ANALYSIS_SETTINGS)
    _update_index_mappings(client.conn, index,
                           {client.t.annotation: ANNOTATION_MAPPING})


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


def _update_index_analysis(conn, name, analysis):
    """Attempt to update the index analysis settings."""
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
    try:
        for doc_type, body in mappings.items():
            conn.indices.put_mapping(index=name,
                                     doc_type=doc_type,
                                     body=body)
    except RequestError as e:
        if not e.error.startswith('MergeMappingException'):
            raise

        message = ("Elasticsearch index mapping cannot be automatically "
                   "updated! Please reindex it. You may find the `hypothesis "
                   "search reindex` command helpful.")
        log.critical(message)
        raise RuntimeError(message)


def _random_id():
    """Generate a short random hex string."""
    return binascii.hexlify(os.urandom(4)).decode()
