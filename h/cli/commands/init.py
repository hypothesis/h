# -*- coding: utf-8 -*-

import logging
import os

import alembic.config
import alembic.command
import click
import sqlalchemy

from h import db
from h import search
from h._compat import text_type

log = logging.getLogger(__name__)


@click.command()
@click.pass_context
def init(ctx):
    # In production environments a short ES request timeout is typically set.
    # Commands to initialize the index may take longer than this, so override
    # any custom timeout with a high value.
    os.environ["ELASTICSEARCH_CLIENT_TIMEOUT"] = "30"

    request = ctx.obj["bootstrap"]()

    _init_db(request.registry.settings)
    _init_search(request.registry.settings)


def _init_db(settings):
    engine = db.make_engine(settings)

    # If the alembic_version table is present, then the database is managed by
    # alembic, and we shouldn't call `db.init`.
    try:
        engine.execute("select 1 from alembic_version")
    except sqlalchemy.exc.ProgrammingError:
        log.info("initializing database")
        db.init(
            engine, should_create=True, authority=text_type(settings["h.authority"])
        )

        # Stamp the database with the current schema version so that future
        # migrations start from the correct point.
        alembic_cfg = alembic.config.Config("conf/alembic.ini")
        alembic.command.stamp(alembic_cfg, "head")
    else:
        log.info("detected alembic_version table, skipping db initialization")


def _init_search(settings):
    client = search.get_client(settings)

    log.info("initializing ES6 search index")
    search.init(client, check_icu_plugin=settings.get("es.check_icu_plugin", True))
