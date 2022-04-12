from dataclasses import dataclass

import elasticsearch


@dataclass(frozen=True)
class Client:
    """A wrapper around an Elasticsearch connection with related settings."""

    index: str
    conn: elasticsearch.Elasticsearch
    mapping_type = "annotation"
    # Our existing Elasticsearch 1.x indexes have a single mapping type
    # "annotation". For ES 6 we should change this to the preferred name
    # of "_doc".
    # See https://www.elastic.co/guide/en/elasticsearch/reference/6.x/removal-of-types.html

    def close(self):
        """Close the connection to the Elasticsearch server."""

        # In the latest version of the `elasticsearch` package we could just
        # do `self._conn.close()` but this method is missing in v6, so we have
        # to close the underlying transport directly.
        self.conn.transport.close()


def get_client(settings):
    """Return a client for the Elasticsearch index."""

    extra_settings = {
        "verify_certs": True,
        "max_retries": settings.get("es.client.max_retries", 3),
        "retry_on_timeout": settings.get("es.client.retry_on_timeout", False),
        "timeout": settings.get("es.client.timeout", 10),
    }

    if "es.client_poolsize" in settings:
        extra_settings["maxsize"] = settings["es.client_poolsize"]

    # nb. No AWS credentials here because we assume that if using AWS-managed
    # ES, the cluster lives inside a VPC.
    return Client(
        index=settings["es.index"],
        conn=elasticsearch.Elasticsearch([settings["es.url"]], **extra_settings),
    )
