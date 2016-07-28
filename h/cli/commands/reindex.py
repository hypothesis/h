# -*- coding: utf-8 -*-

import click

from memex.search import index


@click.command()
@click.pass_context
def reindex(ctx):
    """
    Reindex all annotations from the PostgreSQL database to the Elasticsearch index.
    """

    request = ctx.obj['bootstrap']()

    index.reindex(request.db, request.es, request)
