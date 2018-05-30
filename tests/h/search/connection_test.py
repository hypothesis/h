# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
import mock

from elasticsearch_dsl.connections import connections
from elasticsearch_dsl import Index
from elasticsearch.exceptions import ConnectionError

from h import search
from h.search.connection import connect


def remove_connection():
    """Remove elasticsearch connection made in test"""
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

    def test_connect_defaults_to_default_alias(self, connections_):
        connect()

        connections_.create_connection.assert_called_once_with('default',
                                                               hosts=mock.ANY,
                                                               verify_certs=True)

    def test_connect_passes_kwargs_to_create_connection(self, connections_):
        kwargs = {
            'foo': 'bar'
        }
        connect(**kwargs)

        connections_.create_connection.assert_called_once_with('default',
                                                               hosts=mock.ANY,
                                                               verify_certs=True,
                                                               **kwargs)

    def test_connect_does_not_raise_on_invalid_host(self, request):
        request.addfinalizer(remove_connection)

        connections.create_connection(alias='foobar', hosts=['localhost:2323'])

        assert connections.get_connection('foobar')

    def test_it_does_raise_if_bad_connection_is_queried(self, request):
        request.addfinalizer(remove_connection)

        connections.create_connection(alias='foobar', hosts=['localhost:2323'])

        with pytest.raises(ConnectionError):
            Index('whatever', using='foobar').exists()


@pytest.fixture
def connections_(patch):
    return patch('h.search.connection.connections')
