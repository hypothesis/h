# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

import elasticsearch
import elasticsearch1
import elasticsearch_dsl
import elasticsearch1_dsl

from h.search.client import get_client, get_client_old
from h.search.client import Client


ES1_PATH = 'h.search.client.elasticsearch1.Elasticsearch'
ES_PATH = 'h.search.client.elasticsearch.Elasticsearch'


# Make the old get client method just return the es client obj
# as opposed to the custom wrapper class obj.
def get_client_old_wrap(settings):
    return get_client_old(settings).conn


class TestClient(object):
    @pytest.mark.parametrize('elasticsearch', [(elasticsearch, elasticsearch1)])
    def test_it_sets_the_index_and_conn_properties(self, elasticsearch):
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


class TestClientConnection(object):

    @pytest.mark.parametrize('get_client,elasticsearch_dsl',
        [(get_client, elasticsearch_dsl), (get_client_old_wrap, elasticsearch1_dsl)])
    def test_client_connection_successful(self, client, index, User, get_client, elasticsearch_dsl):
        # write
        user = User(meta={'id': 1}, age=34)
        user.save(index='user', using='es')
        # read
        user = User.get(id=1, index='user', using='es')
        assert user.age == 34

    @pytest.fixture
    def User(self, request):
        elasticsearch_dsl = request.getfixturevalue('elasticsearch_dsl')

        class User(elasticsearch_dsl.DocType):
            age = elasticsearch_dsl.Integer()

        return User

    @pytest.fixture
    def client(self, request):
        get_client = request.getfixturevalue('get_client')
        elasticsearch_dsl = request.getfixturevalue('elasticsearch_dsl')
        # create the connection
        settings = {'es.url': 'http://localhost:9201',
                    'es.host': 'http://localhost:9200',
                    'es.index': 'myindex'}
        client = get_client(settings)
        elasticsearch_dsl.connections.connections.add_connection('es', client)
        yield client
        # delete connection
        elasticsearch_dsl.connections.connections.remove_connection('es')

    @pytest.fixture
    def index(self, User, client, request):
        elasticsearch_dsl = request.getfixturevalue('elasticsearch_dsl')
        # create the index
        index = elasticsearch_dsl.Index('user', using='es')
        index.doc_type(User)
        index.create()
        yield index
        # delete index
        index.delete()


class TestGetClient(object):
    @pytest.mark.parametrize('get_client,patch_path',
        [(get_client, ES_PATH),
         (get_client_old, ES1_PATH)])
    def test_initializes_client_with_host(self, settings, patch_path, patched_elasticsearch, get_client):
        get_client(settings)
        args, _ = patched_elasticsearch.call_args
        assert args[0] == ['search.svc']

    @pytest.mark.parametrize('patch_path', ['h.search.client.Client'])
    def test_initializes_client_with_index(self, settings, patch_path, patched_elasticsearch):
        get_client_old(settings)
        args, _ = patched_elasticsearch.call_args
        assert args[1] == 'my-index'

    @pytest.mark.parametrize('key,value,settingkey,get_client,patch_path', [
        ('max_retries', 7, 'es.client.max_retries', get_client, ES_PATH),
        ('retry_on_timeout', True, 'es.client.retry_on_timeout', get_client, ES_PATH),
        ('timeout', 15, 'es.client.timeout', get_client, ES_PATH),
        ('maxsize', 4, 'es.client_poolsize', get_client, ES_PATH),
        ('max_retries', 7, 'es.client.max_retries', get_client_old, ES1_PATH),
        ('retry_on_timeout', True, 'es.client.retry_on_timeout', get_client_old, ES1_PATH),
        ('timeout', 15, 'es.client.timeout', get_client_old, ES1_PATH),
        ('maxsize', 4, 'es.client_poolsize', get_client_old, ES1_PATH),
    ])
    def test_client_configuration(self, settings, patch_path, patched_elasticsearch, key, value, settingkey, get_client):
        settings[settingkey] = value
        get_client(settings)

        _, kwargs = patched_elasticsearch.call_args
        assert kwargs[key] == value

    @pytest.mark.parametrize('get_client,patch_path',
        [(get_client, ES_PATH),
         (get_client_old, ES1_PATH)])
    def test_initialises_aws_auth(self, settings, patch_path, patched_aws_auth, get_client):
        settings.update({'es.aws.access_key_id': 'foo', 'es.aws.secret_access_key': 'bar', 'es.aws.region': 'baz'})
        get_client(settings)

        patched_aws_auth.assert_called_once_with('foo', 'bar', 'baz', 'es')

    @pytest.mark.parametrize('get_client,patch_path',
        [(get_client, ES_PATH),
         (get_client_old, ES1_PATH)])
    def test_sets_aws_auth(self, settings, patch_path, patched_elasticsearch, patched_aws_auth, get_client):
        settings.update({'es.aws.access_key_id': 'foo', 'es.aws.secret_access_key': 'bar', 'es.aws.region': 'baz'})
        get_client(settings)

        _, kwargs = patched_elasticsearch.call_args
        assert kwargs['http_auth'] == patched_aws_auth.return_value

    @pytest.mark.parametrize('get_client,elasticsearch,patch_path',
        [(get_client, elasticsearch, ES_PATH), (get_client_old, elasticsearch1, ES1_PATH)])
    def test_sets_connection_class_for_aws_auth(self, settings, patch_path, patched_elasticsearch, get_client, elasticsearch):
        settings.update({'es.aws.access_key_id': 'foo', 'es.aws.secret_access_key': 'bar', 'es.aws.region': 'baz'})
        get_client(settings)

        _, kwargs = patched_elasticsearch.call_args
        assert kwargs['connection_class'] == elasticsearch.RequestsHttpConnection

    @pytest.mark.parametrize('aws_settings,get_client,patch_path', [
        ({'es.aws.access_key_id': 'foo'}, get_client, ES_PATH),
        ({'es.aws.secret_access_key': 'foo'}, get_client, ES_PATH),
        ({'es.aws.region': 'foo'}, get_client, ES_PATH),
        ({'es.aws.access_key_id': 'foo', 'es.aws.secret_access_key': 'bar'}, get_client, ES_PATH),
        ({'es.aws.access_key_id': 'foo', 'es.aws.region': 'bar'}, get_client, ES_PATH),
        ({'es.aws.secret_access_key': 'foo', 'es.aws.region': 'bar'}, get_client, ES_PATH),
    ])
    def test_ignores_aws_auth_when_settings_missing(self, settings, patch_path, patched_elasticsearch, aws_settings, get_client):
        settings.update(aws_settings)
        get_client(settings)

        _, kwargs = patched_elasticsearch.call_args
        assert 'auth' not in kwargs

    @pytest.fixture
    def settings(self):
        return {
            'es.host': 'search.svc',
            'es.url': 'search.svc',
            'es.index': 'my-index',
        }

    @pytest.fixture
    def patched_elasticsearch(self, patch, request):
        return patch(request.getfixturevalue('patch_path'))

    @pytest.fixture
    def patched_aws_auth(self, patch):
        return patch('h.search.client.AWS4Auth')
