# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from tests.common.fixtures.elasticsearch import es_client
from tests.common.fixtures.elasticsearch import es_index
from tests.common.fixtures.elasticsearch import init_elasticsearch
from tests.common.fixtures.elasticsearch import delete_all_elasticsearch_documents


__all__ = (
    "es_client",
    "es_index",
    "init_elasticsearch",
    "delete_all_elasticsearch_documents",
)
