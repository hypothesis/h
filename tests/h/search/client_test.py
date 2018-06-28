# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

import elasticsearch1
import elasticsearch

from h.search.client import get_client, get_es6_client
from h.search.client import Client


GET_CLIENTS = (get_client, get_es6_client)


class TestClient(object):

    def test_it_sets_the_index_and_conn_properties(self):
        client = Client(host="http://localhost:9200", index="hypothesis")

        assert client.index == "hypothesis"
        assert client.conn

    def test_index_is_read_only(self):
        client = Client(host="http://localhost:9200", index="hypothesis")

        with pytest.raises(AttributeError, match="can't set attribute"):
            client.index = "changed"

    def test_conn_is_read_only(self):
        client = Client(host="http://localhost:9200", index="hypothesis")

        with pytest.raises(AttributeError, match="can't set attribute"):
            client.conn = "changed"

    def test_defaults_to_es1(self):
        client = Client(host="http://localhost:9200", index="hypothesis")

        assert isinstance(client.conn, elasticsearch1.Elasticsearch)

    def test_uses_es6_when_specified(self):
        client = Client(
            host="http://localhost:9200",
            index="hypothesis",
            elasticsearch=elasticsearch)

        assert isinstance(client.conn, elasticsearch.Elasticsearch)


class TestGetClient(object):
    @pytest.mark.parametrize('get_client', GET_CLIENTS)
    def test_initializes_client_with_host(self, settings, get_client, patched_client):
        get_client(settings)
        args, _ = patched_client.call_args
        assert args[0] == 'search.svc'

    @pytest.mark.parametrize('get_client', GET_CLIENTS)
    def test_initializes_client_with_index(self, settings, get_client, patched_client):
        get_client(settings)
        args, _ = patched_client.call_args
        assert args[1] == 'my-index'

    @pytest.mark.parametrize('key,value,settingkey,get_client', [
        ('max_retries', 7, 'es.client.max_retries', get_client),
        ('retry_on_timeout', True, 'es.client.retry_on_timeout', get_client),
        ('timeout', 15, 'es.client.timeout', get_client),
        ('maxsize', 4, 'es.client_poolsize', get_client),
        ('max_retries', 7, 'es.client.max_retries', get_es6_client),
        ('retry_on_timeout', True, 'es.client.retry_on_timeout', get_es6_client),
        ('timeout', 15, 'es.client.timeout', get_es6_client),
        ('maxsize', 4, 'es.client_poolsize', get_es6_client),
    ])
    def test_client_configuration(self, settings, get_client, patched_client, key, value, settingkey):
        settings[settingkey] = value
        get_client(settings)

        _, kwargs = patched_client.call_args
        assert kwargs[key] == value

    def test_initialises_aws_auth(self, settings, patched_aws_auth):
        settings.update({'es.aws.access_key_id': 'foo', 'es.aws.secret_access_key': 'bar', 'es.aws.region': 'baz'})
        get_client(settings)

        patched_aws_auth.assert_called_once_with('foo', 'bar', 'baz', 'es')

    def test_sets_aws_auth(self, settings, patched_client, patched_aws_auth):
        settings.update({'es.aws.access_key_id': 'foo', 'es.aws.secret_access_key': 'bar', 'es.aws.region': 'baz'})
        get_client(settings)

        _, kwargs = patched_client.call_args
        assert kwargs['http_auth'] == patched_aws_auth.return_value

    def test_sets_connection_class_for_aws_auth(self, settings, patched_client):
        settings.update({'es.aws.access_key_id': 'foo', 'es.aws.secret_access_key': 'bar', 'es.aws.region': 'baz'})
        get_client(settings)

        _, kwargs = patched_client.call_args
        assert kwargs['connection_class'] == elasticsearch1.RequestsHttpConnection

    @pytest.mark.parametrize('aws_settings', [
        {'es.aws.access_key_id': 'foo'},
        {'es.aws.secret_access_key': 'foo'},
        {'es.aws.region': 'foo'},
        {'es.aws.access_key_id': 'foo', 'es.aws.secret_access_key': 'bar'},
        {'es.aws.access_key_id': 'foo', 'es.aws.region': 'bar'},
        {'es.aws.secret_access_key': 'foo', 'es.aws.region': 'bar'},
    ])
    def test_ignores_aws_auth_when_settings_missing(self, settings, patched_client, aws_settings):
        settings.update(aws_settings)
        get_client(settings)

        _, kwargs = patched_client.call_args
        assert 'auth' not in kwargs

    @pytest.fixture
    def settings(self):
        return {
            'es.host': 'search.svc',
            'es.url': 'search.svc',
            'es.index': 'my-index',
        }

    @pytest.fixture
    def patched_client(self, patch):
        return patch('h.search.client.Client')

    @pytest.fixture
    def patched_aws_auth(self, patch):
        return patch('h.search.client.AWS4Auth')
