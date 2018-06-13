# -*- coding: utf-8 -*-

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
    Reindex all annotations in the old search cluster.

    Creates a new search index from the data in PostgreSQL and atomically
    updates the index alias. This requires that the index is aliased already,
    and will raise an error if it is not.
    """
    _reindex_old(ctx)


@search.command()
@click.pass_context
def reindex_es6(ctx):
    """
    Reindex all annotations in the new search cluster.
    """
    _reindex_es6(ctx)


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


def _reindex_old(ctx):
    """
    Reindex all annotations in the old cluster.

    Creates a new search index from the data in PostgreSQL and atomically
    updates the index alias. This requires that the index is aliased already,
    and will raise an error if it is not.
    """

    os.environ['ELASTICSEARCH_CLIENT_TIMEOUT'] = '30'

    request = ctx.obj['bootstrap']()

    indexer.reindex(request.db, request.es, request)


def _reindex_es6(ctx):
    """
    Reindex all annotations in the new cluster.
    """
    os.environ['ELASTICSEARCH_CLIENT_TIMEOUT'] = '30'

    request = ctx.obj['bootstrap']()

    indexer.reindex(request.db, request.es6, request)


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
