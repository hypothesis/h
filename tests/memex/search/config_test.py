# -*- coding: utf-8 -*-

import itertools
import re
import urllib

import mock
import pytest
from elasticsearch.exceptions import NotFoundError

from memex.search.config import (
    ANNOTATION_ANALYSIS,
    init,
    get_aliased_index,
    update_aliased_index,
)


def test_strip_scheme_char_filter():
    f = ANNOTATION_ANALYSIS['char_filter']['strip_scheme']
    p = f['pattern']
    r = f['replacement']
    assert(re.sub(p, r, 'http://ping/pong#hash') == 'ping/pong#hash')
    assert(re.sub(p, r, 'chrome-extension://1234/a.js') == '1234/a.js')
    assert(re.sub(p, r, 'a+b.c://1234/a.js') == '1234/a.js')
    assert(re.sub(p, r, 'uri:x-pdf:1234') == 'x-pdf:1234')
    assert(re.sub(p, r, 'example.com') == 'example.com')
    # This is ambiguous, and possibly cannot be expected to work.
    # assert(re.sub(p, r, 'localhost:5000') == 'localhost:5000')


def test_path_url_filter():
    patterns = ANNOTATION_ANALYSIS['filter']['path_url']['patterns']
    assert(captures(patterns, 'example.com/foo/bar?query#hash') == [
        'example.com/foo/bar'
    ])
    assert(captures(patterns, 'example.com/foo/bar/') == [
        'example.com/foo/bar/'
    ])


def test_rstrip_slash_filter():
    p = ANNOTATION_ANALYSIS['filter']['rstrip_slash']['pattern']
    r = ANNOTATION_ANALYSIS['filter']['rstrip_slash']['replacement']
    assert(re.sub(p, r, 'example.com/') == 'example.com')
    assert(re.sub(p, r, 'example.com/foo/bar/') == 'example.com/foo/bar')


def test_uri_part_tokenizer():
    text = 'http://a.b/foo/bar?c=d#stuff'
    pattern = ANNOTATION_ANALYSIS['tokenizer']['uri_part']['pattern']
    assert(re.split(pattern, text) == [
        'http', '', '', 'a', 'b', 'foo', 'bar', 'c', 'd', 'stuff'
    ])

    text = urllib.quote_plus(text)
    assert(re.split(pattern, 'http://jump.to/?u=' + text) == [
        'http', '', '', 'jump', 'to', '', 'u',
        'http', '', '', 'a', 'b', 'foo', 'bar', 'c', 'd', 'stuff'
    ])


class TestInit(object):
    def test_configures_index(self, patch):
        configure_index = patch('memex.search.config.configure_index')

        init(mock.sentinel.client)

        configure_index.assert_called_once_with(mock.sentinel.client)


class TestGetAliasedIndex(object):
    def test_returns_underlying_index_name(self, client):
        """If ``index`` is an alias, return the name of the concrete index."""
        client.conn.indices.get_alias.return_value = {
            'target-index': {'aliases': {'foo': {}}},
        }

        assert get_aliased_index(client) == 'target-index'

    def test_returns_none_when_no_alias(self, client):
        """If ``index`` is a concrete index, return None."""
        client.conn.indices.get_alias.side_effect = NotFoundError('test', 'test desc')

        assert get_aliased_index(client) is None

    def test_raises_if_aliased_to_multiple_indices(self, client):
        """Raise if ``index`` is an alias pointing to multiple indices."""
        client.conn.indices.get_alias.return_value = {
            'index-one': {'aliases': {'foo': {}}},
            'index-two': {'aliases': {'foo': {}}},
        }

        with pytest.raises(RuntimeError):
            get_aliased_index(client)


class TestUpdateAliasedIndex(object):
    def test_updates_index_atomically(self, client):
        """Update the alias atomically."""
        client.conn.indices.get_alias.return_value = {
            'old-target': {'aliases': {'foo': {}}},
        }

        update_aliased_index(client, 'new-target')

        client.conn.indices.update_aliases.assert_called_once_with(body={
            'actions': [
                {'add': {'index': 'new-target', 'alias': 'foo'}},
                {'remove': {'index': 'old-target', 'alias': 'foo'}},
            ],
        })

    def test_raises_if_called_for_concrete_index(self, client):
        """Raise if called for a concrete index."""
        client.conn.indices.get_alias.side_effect = NotFoundError('test', 'test desc')

        with pytest.raises(RuntimeError):
            update_aliased_index(client, 'new-target')


def captures(patterns, text):
    return list(itertools.chain(*(groups(p, text) for p in patterns)))


def groups(pattern, text):
    return re.search(pattern, text).groups() or []


@pytest.fixture
def client():
    client = mock.Mock(spec_set=['conn', 'index'])
    client.index = 'foo'
    return client
