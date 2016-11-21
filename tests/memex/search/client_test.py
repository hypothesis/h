# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from elasticsearch.exceptions import NotFoundError

from memex.search.client import Client


class TestClient(object):
    def test_get_aliased_index(self, conn):
        """If ``index`` is an alias, return the name of the concrete index."""
        conn.indices.get_alias.return_value = {
            'target-index': {'aliases': {'foo': {}}},
        }
        client = Client('localhost', 'foo')

        assert client.get_aliased_index() == 'target-index'

    def test_get_aliased_index_no_alias(self, conn):
        """If ``index`` is a concrete index, return None."""
        conn.indices.get_alias.side_effect = NotFoundError('test', 'test desc')
        client = Client('localhost', 'foo')

        assert client.get_aliased_index() is None

    def test_get_aliased_index_multiple_indices(self, conn):
        """Raise if ``index`` is an alias pointing to multiple indices."""
        conn.indices.get_alias.return_value = {
            'index-one': {'aliases': {'foo': {}}},
            'index-two': {'aliases': {'foo': {}}},
        }
        client = Client('localhost', 'foo')

        with pytest.raises(RuntimeError):
            client.get_aliased_index()

    def test_update_aliased_index(self, conn):
        """Update the alias atomically."""
        conn.indices.get_alias.return_value = {
            'old-target': {'aliases': {'foo': {}}},
        }
        client = Client('localhost', 'foo')

        client.update_aliased_index('new-target')

        conn.indices.update_aliases.assert_called_once_with(body={
            'actions': [
                {'add': {'index': 'new-target', 'alias': 'foo'}},
                {'remove': {'index': 'old-target', 'alias': 'foo'}},
            ],
        })

    def test_update_aliased_index_with_concrete_index(self, conn):
        """Raise if called for a concrete index."""
        conn.indices.get_alias.side_effect = NotFoundError('test', 'test desc')
        client = Client('localhost', 'foo')

        with pytest.raises(RuntimeError):
            client.update_aliased_index('new-target')

    @pytest.fixture
    def conn(self, patch):
        es = patch('memex.search.client.Elasticsearch')
        conn = es.return_value
        conn.indices = mock.Mock()
        return conn
