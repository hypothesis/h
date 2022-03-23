from typing import Tuple

import elasticsearch


class Client:
    """
    A convenience wrapper around a connection to Elasticsearch.

    :param host: Elasticsearch host URL
    :param index: index name
    :param elasticsearch: Elasticsearch library defaulted to elasticsearch
    """

    def __init__(
        self, host, index, elasticsearch=elasticsearch, **kwargs
    ):  # pylint: disable=redefined-outer-name
        self._version = elasticsearch.__version__
        self._index = index
        self._conn = elasticsearch.Elasticsearch([host], **kwargs)

        # The ES server version is initialized lazily, to avoid making a request
        # to the server until it is needed.
        self._server_version = None

    def close(self):
        """Close the connection to the Elasticsearch server."""

        # In the latest version of the `elasticsearch` package we could just
        # do `self._conn.close()` but this method is missing in v6 so we have
        # to close the underlying transport directly.
        self._conn.transport.close()

    @property
    def index(self):
        return self._index

    @property
    def conn(self):
        return self._conn

    @property
    def mapping_type(self):
        """
        Return the name of the index's mapping type (aka. document type).

        In Elasticsearch <= 6.x our indexes have a single mapping type called
        "annotation". In ES >= 7.x the concept of mapping types has been
        removed but indexing APIs use the dummy value `_doc`.

        See https://www.elastic.co/guide/en/elasticsearch/reference/6.x/removal-of-types.html
        """
        if self.server_version < (7, 0, 0):
            return "annotation"
        return "_doc"

    @property
    def version(self):
        """Get the version of the elasticsearch library."""
        return self._version

    @property
    def server_version(self) -> Tuple[int, int, int]:
        """Get the version of the connected Elasticsearch cluster."""
        if not self._server_version:
            version_str = self._conn.info()["version"]["number"]

            # We assume the ES version has 3 parts. This has been true of all
            # non pre-release versions historically.
            major, minor, patch = [int(part) for part in version_str.split(".")]

            self._server_version = (major, minor, patch)
        return self._server_version


def _get_client_settings(settings):
    kwargs = {}
    kwargs["max_retries"] = settings.get("es.client.max_retries", 3)
    kwargs["retry_on_timeout"] = settings.get("es.client.retry_on_timeout", False)
    kwargs["timeout"] = settings.get("es.client.timeout", 10)

    if "es.client_poolsize" in settings:
        kwargs["maxsize"] = settings["es.client_poolsize"]

    kwargs["verify_certs"] = True
    return kwargs


def get_client(settings):
    """Return a client for the Elasticsearch index."""
    host = settings["es.url"]
    index = settings["es.index"]
    kwargs = _get_client_settings(settings)
    # nb. No AWS credentials here because we assume that if using AWS-managed
    # ES, the cluster lives inside a VPC.
    return Client(host, index, **kwargs)
