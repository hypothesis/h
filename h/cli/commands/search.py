import os

import click

from h import indexer
from h.search import config


@click.group()
def search():
    """Manage search index."""


@search.command()
@click.pass_context
def reindex(ctx):
    """
    Reindex all annotations.

    Creates a new search index from the data in PostgreSQL and atomically
    updates the index alias. This requires that the index is aliased already,
    and will raise an error if it is not.
    """
    os.environ["ELASTICSEARCH_CLIENT_TIMEOUT"] = "30"

    request = ctx.obj["bootstrap"]()

    es_client = request.es

    es_server_version = es_client.conn.info()["version"]["number"]
    click.echo(f"reindexing into Elasticsearch {es_server_version} cluster")

    indexer.reindex(request.db, es_client, request)


@search.command("update-settings")
@click.pass_context
def update_settings(ctx):
    """
    Attempt to update mappings and settings in elasticsearch.

    Attempts to update mappings and index settings. This may fail if the
    pending changes to mappings are not compatible with the current index. In
    this case you will likely need to reindex.
    """
    request = ctx.obj["bootstrap"]()

    try:
        config.update_index_settings(request.es)
    except RuntimeError as exc:
        raise click.ClickException(str(exc))
