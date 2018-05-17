# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

import h.search.index


@pytest.fixture
def index(es_client, pyramid_request):
    def _index(*annotations):
        """Index the given annotation(s) into Elasticsearch."""
        for annotation in annotations:
            h.search.index.index(es_client, annotation, pyramid_request)
        es_client.conn.indices.refresh(index=es_client.index)
    return _index
