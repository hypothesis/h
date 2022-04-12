from unittest.mock import MagicMock, create_autospec, sentinel

import pytest
from elasticsearch import Elasticsearch
from h_matchers import Any

from h.search.client import Client, get_client


class TestClient:
    def test_close(self, client, conn):
        client.close()

        conn.transport.close.assert_called_once_with()

    @pytest.fixture
    def conn(self):
        # The ES library really confuses autospeccing
        return create_autospec(Elasticsearch, instance=True, transport=MagicMock())

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
