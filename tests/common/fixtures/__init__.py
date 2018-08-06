# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from tests.common.fixtures.elasticsearch import es6_client, es_connect
from tests.common.fixtures.elasticsearch import init_elasticsearch


__all__ = (
    "es6_client",
    "es_connect",
    "init_elasticsearch",
)
