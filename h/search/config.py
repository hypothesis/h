"""
Index mappings and analysis settings for Elasticsearch, and associated tools.

This module contains the index mappings and analysis settings for data indexed
into Elasticsearch. It also contains some helper functions to create and update
these settings in an Elasticsearch instance.
"""

import binascii
import logging
import os

import elasticsearch

log = logging.getLogger(__name__)


# Elasticsearch type mapping for annotations for ES 6.x and later.
ANNOTATION_MAPPING = {
    # Ignore unknown fields and do not add them to the mapping.
    # This ensures that only fields included in the "properties" section
    # here can be searched against.
    "dynamic": False,
    # Indexed (searchable) fields.
    "properties": {
        "authority": {"type": "keyword"},
        "created": {"type": "date"},
        "deleted": {"type": "boolean"},
        "document": {"enabled": False},  # not indexed
        "group": {"type": "keyword"},
        "id": {"type": "keyword"},
        "nipsa": {"type": "boolean"},
        "quote": {"type": "text", "analyzer": "uni_normalizer"},
        "references": {"type": "keyword"},
        "shared": {"type": "boolean"},
        "hidden": {"type": "boolean"},
        "tags": {"type": "text", "analyzer": "uni_normalizer"},
        "tags_raw": {"type": "keyword"},
        "text": {"type": "text", "analyzer": "uni_normalizer"},
        "target": {
            "properties": {
                "source": {"type": "text", "analyzer": "uri", "copy_to": ["uri"]},
                # We store the 'scope' unanalyzed and only do term filters
                # against this field.
                "scope": {"type": "keyword"},
                "selector": {
                    "properties": {
                        # Open Annotation TextQuoteSelector
                        "exact": {"copy_to": "quote", "type": "text", "index": False}
                    }
                },
            }
        },
        "thread_ids": {"type": "keyword"},
        "updated": {"type": "date"},
        "uri": {
            "type": "text",
            "analyzer": "uri",
            "fields": {"parts": {"type": "text", "analyzer": "uri_parts"}},
        },
        "user": {"type": "text", "analyzer": "user"},
        "user_raw": {"type": "keyword"},
    },
}

# Filter and tokenizer definitions for ES 6.x and greater mappings.
ANALYSIS_SETTINGS = {
    "char_filter": {
        "strip_scheme": {
            "type": "pattern_replace",
            "pattern": r"^(?:[A-Za-z][A-Za-z.+-]+:)?/{0,3}",
            "replacement": "",
        }
    },
    "filter": {
        "path_url": {
            "type": "pattern_capture",
            "preserve_original": "false",
            "patterns": [r"([0-9.\-A-Za-z]+(?::\d+)?(?:/[^?#]*))?"],
        },
        "rstrip_slash": {"type": "pattern_replace", "pattern": "/$", "replacement": ""},
        "user": {
            "type": "pattern_capture",
            "preserve_original": "true",
            "patterns": ["^acct:((.+)@.*)$"],
        },
    },
    "tokenizer": {
        "uri_part": {
            "type": "pattern",
            "pattern": r"[#+/:=?.-]|(?:%2[3BF])|(?:%3[ADF])",
        }
    },
    "analyzer": {
        "uri": {
            "tokenizer": "keyword",
            "char_filter": ["strip_scheme"],
            "filter": ["path_url", "rstrip_slash", "lowercase"],
        },
        "uri_parts": {"tokenizer": "uri_part", "filter": ["unique"]},
        "user": {"tokenizer": "keyword", "filter": ["user", "lowercase"]},
        "uni_normalizer": {"tokenizer": "icu_tokenizer", "filter": ["icu_folding"]},
    },
}


def init(client, check_icu_plugin=True):
    """Initialise Elasticsearch, creating necessary indices and aliases."""
    # Ensure the ICU analysis plugin is installed
    if check_icu_plugin:
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
    index_name = client.index + "-" + _random_id()
    mapping = ANNOTATION_MAPPING
    client.conn.indices.create(
        index_name,
        body={
            "mappings": {client.mapping_type: mapping},
            "settings": {"analysis": ANALYSIS_SETTINGS},
        },
    )

    return index_name


def get_aliased_index(client):
    """
    Fetch the name of the underlying index.

    Returns ``None`` if the index is not aliased or does not exist.
    """
    try:
        result = client.conn.indices.get_alias(name=client.index)
    except elasticsearch.exceptions.NotFoundError:  # no alias with that name
        return None
    if len(result) > 1:
        raise RuntimeError(
            "We don't support managing aliases that "
            "point to multiple indices at the moment!"
        )
    return list(result.keys())[0]


def update_aliased_index(client, new_target):
    """
    Update the alias to point to a new target index.

    Will raise `RuntimeError` if the index is not aliased or does not
    exist.
    """
    old_target = get_aliased_index(client)
    if old_target is None:
        raise RuntimeError(
            "Cannot update aliased index for index that " "is not already aliased."
        )

    client.conn.indices.update_aliases(
        body={
            "actions": [
                {"add": {"index": new_target, "alias": client.index}},
                {"remove": {"index": old_target, "alias": client.index}},
            ]
        }
    )


def delete_index(client, index_name):
    """
    Delete an unused index.

    This must be an actual index and not an alias.
    """

    client.conn.indices.delete(index=index_name)


def update_index_settings(client):
    """
    Update the index settings (analysis and mappings) to their current state.

    May raise if Elasticsearch throws a MergeMappingException indicating that
    the index cannot be updated without reindexing.
    """
    index = get_aliased_index(client)
    mapping = ANNOTATION_MAPPING

    _update_index_analysis(client.conn, index, ANALYSIS_SETTINGS)
    _update_index_mappings(client.conn, index, client.mapping_type, mapping)


def _ensure_icu_plugin(conn):
    """Ensure that the ICU analysis plugin is installed for ES."""
    # Pylint issue #258: https://bitbucket.org/logilab/pylint/issue/258
    #
    # pylint: disable=unexpected-keyword-arg
    names = [x.strip() for x in conn.cat.plugins(h="component").split("\n")]
    if "analysis-icu" not in names:
        message = (
            "The Elasticsearch ICU Analysis plugin is not installed. "
            "Refer to "
            "https://github.com/elastic/elasticsearch-analysis-icu "
            "for installation instructions."
        )
        raise RuntimeError(message)


def _update_index_analysis(conn, name, analysis):
    """Attempt to update the index analysis settings."""
    settings = conn.indices.get_settings(index=name)
    existing = settings[name]["settings"]["index"].get("analysis", {})
    if existing != analysis:
        try:  # pylint: disable=too-many-try-statements
            conn.indices.close(index=name)
            conn.indices.put_settings(index=name, body={"analysis": analysis})
        finally:
            conn.indices.open(index=name)


def _update_index_mappings(conn, name, doc_type, mapping):
    """Attempt to update the index mappings."""
    try:
        conn.indices.put_mapping(index=name, doc_type=doc_type, body=mapping)
    except elasticsearch.exceptions.RequestError as err:
        if not err.error.startswith("MergeMappingException"):
            raise

        message = (
            "Elasticsearch index mapping cannot be automatically "
            "updated! Please reindex it. You may find the `hypothesis "
            "search reindex` command helpful."
        )
        log.critical(message)
        raise RuntimeError(message) from err


def _random_id():
    """Generate a short random hex string."""
    return binascii.hexlify(os.urandom(4)).decode()
