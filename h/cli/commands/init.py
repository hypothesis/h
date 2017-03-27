# -*- coding: utf-8 -*-

import logging

import click
import sqlalchemy

from h import db
from h import models  # noqa: import to ensure memex model base class is set
from h import search

log = logging.getLogger(__name__)


@click.command()
@click.pass_context
def init(ctx):
    request = ctx.obj['bootstrap']()

    _init_db(request.registry.settings)
    _init_search(request.registry.settings)


def _init_db(settings):
    engine = db.make_engine(settings)

    # If the alembic_version table is present, then the database is managed by
    # alembic, and we shouldn't call `db.init`.
    try:
        engine.execute('select 1 from alembic_version')
    except sqlalchemy.exc.ProgrammingError:
        log.info("initializing database")
        db.init(engine, should_create=True)
    else:
        log.info("detected alembic_version table, skipping db initialization")


def _init_search(settings):
    client = search.get_client(settings)

    log.info("initializing search index")
    search.init(client)
