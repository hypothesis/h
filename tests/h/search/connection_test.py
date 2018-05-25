# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from elasticsearch_dsl.connections import connections
from h import search
from h.search.connection import connect


class TestConnection(object):
    def test_connect_is_available_in_search_api(self):
        assert connect == search.connect

    def test_connect_creates_default_connection(self):
        # search.connect is invoked as part of test bootstrapping
        # so the connection should already be established
        assert connections.get_connection()
        assert connections.get_connection('default')
        assert connections.get_connection() == connections.get_connection('default')
