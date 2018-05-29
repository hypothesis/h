# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

import pytest

from h import search

ELASTICSEARCH_HOST = os.environ.get("ELASTICSEARCH_HOST", "http://localhost:9200")
ELASTICSEARCH_INDEX = "hypothesis-test"
ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9201")


@pytest.fixture
def es_client():
    """A :py:class:`h.search.client.Client` for the test search index."""
    client = _es_client()

    yield client

    # Delete everything from the test search index after each test.
    client.conn.delete_by_query(index=client.index, body={"query": {"match_all": {}}})


@pytest.fixture
def es_connect():
    # TODO handle deleting things out of this connection's index as
    # the `es_client` fixture does
    search.connect(hosts=[ELASTICSEARCH_URL])


@pytest.fixture(scope="session", autouse=True)
def init_elasticsearch(request):
    """Initialize the test (old) Elasticsearch index once per test session."""
    client = _es_client()
    # Initialize the test search index.
    search.init(es_client)
    """Connect to the newer v6.x instance of Elasticsearch once per test session"""
    es_connect()


    yield es_client

    # Delete the test search index at the end of the test run.
    if es_client.conn.indices.exists(index=ELASTICSEARCH_INDEX):
        es_client.conn.indices.delete(index=ELASTICSEARCH_INDEX)
    # Todo: call es_disconnect to disconnect from v6.x es.


def _es_client():
    """Return a :py:class:`h.search.client.Client` for the test search index."""
    return search.get_client({"es.host": ELASTICSEARCH_HOST, "es.index": ELASTICSEARCH_INDEX})
