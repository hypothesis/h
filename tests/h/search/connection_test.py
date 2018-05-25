# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from elasticsearch_dsl.connections import connections
from h import search
from h.search.connection import connect


def remove_connection():
    connections.remove_connection('foobar')


class TestConnection(object):
    def test_connect_is_available_in_search_api(self):
        assert connect == search.connect

    def test_connect_creates_default_connection(self):
        # search.connect is invoked as part of test bootstrapping
        # so the connection should already be established
        assert connections.get_connection()
        assert connections.get_connection('default')
        assert connections.get_connection() == connections.get_connection('default')

    def test_connect_allows_additional_aliases(self, request):
        request.addfinalizer(remove_connection)

        connections.create_connection(alias='foobar')

        assert connections.get_connection('foobar')
