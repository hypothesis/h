# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from elasticsearch_dsl.connections import connections
from elasticsearch_dsl import Index

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

    def test_connect_does_not_raise_on_invalid_host(self, request):
        request.addfinalizer(remove_connection)

        connections.create_connection(alias='foobar', hosts=['localhost:2323'])

        assert connections.get_connection('foobar')

    def test_it_does_raise_if_bad_connection_is_queried(self, request):
        request.addfinalizer(remove_connection)

        connections.create_connection(alias='foobar', hosts=['localhost:2323'])
        with pytest.raises(Exception) as e:
            Index('whatever', using='foobar').exists()

        assert e.typename == 'ConnectionError'
