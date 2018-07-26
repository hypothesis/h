# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from tests.common.fixtures.elasticsearch import es_client, es6_client, es_connect
from tests.common.fixtures.elasticsearch import init_elasticsearch
from tests.common.fixtures.elasticsearch import delete_all_elasticsearch_documents


__all__ = (
    "es_client",
    "es6_client",
    "es_connect",
    "init_elasticsearch",
    "delete_all_elasticsearch_documents",
)
