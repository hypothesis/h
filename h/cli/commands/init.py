# -*- coding: utf-8 -*-

import logging

import click
from elasticsearch_dsl import connections
import sqlalchemy

from h import db
from h import search
from h._compat import text_type

log = logging.getLogger(__name__)


@click.command()
@click.pass_context
def init(ctx):
    request = ctx.obj['bootstrap']()
    settings = request.registry.settings
    _init_db(settings)
    _init_search_old(settings)
    _init_search(settings)


def _init_db(settings):
    engine = db.make_engine(settings)

    # If the alembic_version table is present, then the database is managed by
    # alembic, and we shouldn't call `db.init`.
    try:
        engine.execute('select 1 from alembic_version')
    except sqlalchemy.exc.ProgrammingError:
        log.info("initializing database")
        db.init(engine, should_create=True, authority=text_type(settings['h.authority']))
    else:
        log.info("detected alembic_version table, skipping db initialization")


def _init_search_old(settings):
    client = search.get_client_old(settings)

    log.info("initializing search index")
    search.init(client)


def _init_search(settings):
    # Set the elasticsearch client connection as the default connection.
    connections.add_connection('default', search.get_client(settings))
