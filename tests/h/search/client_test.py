# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from elasticsearch1 import RequestsHttpConnection

from h.search.client import get_client
from h.search.client import Client


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


class TestGetClient(object):
    def test_initializes_client_with_host(self, settings, patched_client):
        get_client(settings)
        args, _ = patched_client.call_args
        assert args[0] == 'search.svc'

    def test_initializes_client_with_index(self, settings, patched_client):
        get_client(settings)
        args, _ = patched_client.call_args
        assert args[1] == 'my-index'

    @pytest.mark.parametrize('key,value,settingkey', [
        ('max_retries', 7, 'es.client.max_retries'),
        ('retry_on_timeout', True, 'es.client.retry_on_timeout'),
        ('timeout', 15, 'es.client.timeout'),
        ('maxsize', 4, 'es.client_poolsize'),
    ])
    def test_client_configuration(self, settings, patched_client, key, value, settingkey):
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
        assert kwargs['connection_class'] == RequestsHttpConnection

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
            'es.index': 'my-index',
        }

    @pytest.fixture
    def patched_client(self, patch):
        return patch('h.search.client.Client')

    @pytest.fixture
    def patched_aws_auth(self, patch):
        return patch('h.search.client.AWS4Auth')
