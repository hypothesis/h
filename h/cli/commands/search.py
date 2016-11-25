# -*- coding: utf-8 -*-

import click

from memex.search import index


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

    request = ctx.obj['bootstrap']()

    index.reindex(request.db, request.es, request)
