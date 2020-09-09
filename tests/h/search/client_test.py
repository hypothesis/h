import elasticsearch
import pytest

from h.search.client import Client, get_client


class TestClient:
    def test_it_sets_the_index_property(self):
        client = Client(host="http://localhost:9200", index="hypothesis")

        assert client.index == "hypothesis"

    def test_it_sets_the_version_property(self):
        client = Client(host="http://localhost:9200", index="hypothesis")

        assert client.version >= (6, 4, 0) and client.version < (7, 0, 0)

    def test_it_sets_the_conn_property(self):
        client = Client(host="http://localhost:9200", index="hypothesis")

        assert isinstance(client.conn, elasticsearch.Elasticsearch)

    def test_index_is_read_only(self):
        client = Client(host="http://localhost:9200", index="hypothesis")

        with pytest.raises(AttributeError, match="can't set attribute"):
            client.index = "changed"

    def test_conn_is_read_only(self):
        client = Client(host="http://localhost:9200", index="hypothesis")

        with pytest.raises(AttributeError, match="can't set attribute"):
            client.conn = "changed"


class TestGetClient:
    def test_initializes_client_with_host(self, settings, patched_client):
        get_client(settings)
        args, _ = patched_client.call_args
        assert args[0] == "search.svc"

    def test_initializes_client_with_index(self, settings, patched_client):
        get_client(settings)
        args, _ = patched_client.call_args
        assert args[1] == "my-index"

    @pytest.mark.parametrize(
        "key,value,settingkey",
        [
            ("max_retries", 7, "es.client.max_retries"),
            ("retry_on_timeout", True, "es.client.retry_on_timeout"),
            ("timeout", 15, "es.client.timeout"),
            ("maxsize", 4, "es.client_poolsize"),
            ("max_retries", 7, "es.client.max_retries"),
            ("retry_on_timeout", True, "es.client.retry_on_timeout"),
            ("timeout", 15, "es.client.timeout"),
            ("maxsize", 4, "es.client_poolsize"),
        ],
    )
    def test_client_configuration(
        self, settings, patched_client, key, value, settingkey
    ):
        settings[settingkey] = value
        get_client(settings)

        _, kwargs = patched_client.call_args
        assert kwargs[key] == value

    @pytest.fixture
    def settings(self):
        return {"es.url": "search.svc", "es.index": "my-index"}

    @pytest.fixture
    def patched_client(self, patch):
        return patch("h.search.client.Client")
