from unittest.mock import MagicMock, create_autospec, sentinel

import pytest
from elasticsearch import Elasticsearch
from h_matchers import Any
from packaging.version import Version

from h.search.client import Client, get_client

pytestmark = [
    pytest.mark.xdist_group("elasticsearch"),
    pytest.mark.usefixtures("init_elasticsearch"),
]


class TestClient:
    def test_close(self, client, conn):
        client.close()

        conn.transport.close.assert_called_once_with()

    @pytest.mark.parametrize(
        "version,mapping_type",
        (("6.9.9", "annotation"), ("7.0.0", "_doc"), ("7.0.1", "_doc")),
    )
    def test_mapping_type(self, client, conn, version, mapping_type):
        conn.info.return_value = {"version": {"number": version}}

        assert client.mapping_type == mapping_type

    def test_server_version(self, client):
        assert client.server_version == Version("1.2.3")

    @pytest.fixture
    def conn(self):
        # The ES library really confuses autospeccing
        conn = create_autospec(Elasticsearch, instance=True, transport=MagicMock())
        conn.info.return_value = {"version": {"number": "1.2.3"}}
        return conn

    @pytest.fixture
    def client(self, conn):
        return Client(index=sentinel.index, conn=conn)


class TestGetClient:
    @pytest.mark.parametrize(
        "settings,expected",
        (
            (
                # Check all the defaults
                {},
                {
                    "verify_certs": True,
                    "max_retries": 3,
                    "retry_on_timeout": False,
                    "timeout": 10,
                },
            ),
            ({"es.client_poolsize": 4}, {"maxsize": 4}),
            ({"es.client.timeout": 15}, {"timeout": 15}),
            ({"es.client.retry_on_timeout": True}, {"retry_on_timeout": True}),
            ({"es.client.max_retries": 7}, {"max_retries": 7}),
        ),
    )
    def test_it(self, Client, Elasticsearch, settings, expected):
        client = get_client(
            {"es.url": sentinel.url, "es.index": sentinel.index, **settings}
        )

        args, kwargs = Elasticsearch.call_args
        assert args, kwargs == (([sentinel.url],), Any.dict.containing(expected))

        Client.assert_called_once_with(
            index=sentinel.index, conn=Elasticsearch.return_value
        )
        assert client == Client.return_value

    @pytest.fixture
    def Elasticsearch(self, patch):
        return patch("h.search.client.elasticsearch.Elasticsearch")

    @pytest.fixture
    def Client(self, patch):
        return patch("h.search.client.Client")
