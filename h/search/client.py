from dataclasses import dataclass
from functools import cached_property

import elasticsearch
from packaging.version import Version


@dataclass(frozen=True)
class Client:
    """A wrapper around an Elasticsearch connection with related settings."""

    index: str
    conn: elasticsearch.Elasticsearch

    def close(self):
        """Close the connection to the Elasticsearch server."""

        # In the latest version of the `elasticsearch` package we could just
        # do `self._conn.close()` but this method is missing in v6, so we have
        # to close the underlying transport directly.
        self.conn.transport.close()

    @cached_property
    def mapping_type(self):
        """Get the name of the index's mapping type (aka. document type)."""
        # In Elasticsearch <= 6.x our indexes have a single mapping type called
        # "annotation". In ES >= 7.x the concept of mapping types has been
        # removed but indexing APIs use the dummy value `_doc`.
        # See: https://www.elastic.co/guide/en/elasticsearch/reference/6.x/removal-of-types.html

        if self.server_version < Version("7.0.0"):
            return "annotation"

        return "_doc"

    @cached_property
    def server_version(self) -> Version:
        """Get the version of the connected Elasticsearch cluster."""

        return Version(self.conn.info()["version"]["number"])


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
