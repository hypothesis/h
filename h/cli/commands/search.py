# -*- coding: utf-8 -*-

import os

import click

from h import indexer
from h.search import config


@click.group()
def search():
    """Manage search index."""


@search.command()
@click.option('--es6', is_flag=True, help='Reindex into the Elasticsearch 6 cluster')
@click.option('--parallel/--no-parallel', default=False,
              help='Use Celery tasks to reindex annotations in parallel.')
@click.pass_context
def reindex(ctx, es6, parallel):
    """
    Reindex all annotations.

    Creates a new search index from the data in PostgreSQL and atomically
    updates the index alias. This requires that the index is aliased already,
    and will raise an error if it is not.

    Reindex into the Elasticsearch 1 cluster by default, unless the `--es6`
    flag is set.
    """
    os.environ['ELASTICSEARCH_CLIENT_TIMEOUT'] = '30'

    request = ctx.obj['bootstrap']()

    if es6:
        es_client = request.es6
    else:
        es_client = request.es

    es_server_version = es_client.conn.info()['version']['number']
    click.echo('reindexing into Elasticsearch {} cluster'.format(es_server_version))

    indexer.reindex(request.db, es_client, request, parallel=parallel)


@search.command('update-settings')
@click.pass_context
def update_settings(ctx):
    """
    Attempt to update mappings and settings in all clusters.

    Attempts to update mappings and index settings. This may fail if the
    pending changes to mappings are not compatible with the current index. In
    this case you will likely need to reindex.
    """
    _update_settings_old(ctx)


def _update_settings_old(ctx):
    """
    Attempt to update mappings and settings in the old cluster.

    Attempts to update mappings and index settings. This may fail if the
    pending changes to mappings are not compatible with the current index. In
    this case you will likely need to reindex.
    """

    request = ctx.obj['bootstrap']()

    try:
        config.update_index_settings(request.es)
    except RuntimeError as e:
        raise click.ClickException(str(e))
