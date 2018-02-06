from __future__ import with_statement

import logging
import os

from alembic import context
from sqlalchemy import engine_from_config, pool

from h import db
from h.settings import database_url

# Import all model modules here in order to populate the metadata
from h import models  # noqa

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config


def configure_logging():
    logging.basicConfig(format='%(asctime)s %(process)d %(name)s [%(levelname)s] '
                               '%(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)

    if 'DEBUG_QUERY' in os.environ:
        level = logging.INFO
        if os.environ.get('DEBUG_QUERY') == 'trace':
            level = logging.DEBUG
        logging.getLogger('sqlalchemy.engine').setLevel(level)


def get_database_url():
    if 'DATABASE_URL' in os.environ:
        return database_url(os.environ['DATABASE_URL'])
    return config.get_main_option("sqlalchemy.url")


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(url=get_database_url(),
                      transaction_per_migration=True)

    context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    section = config.config_ini_section

    config.set_section_option(section, 'sqlalchemy.url', get_database_url())

    engine = engine_from_config(
        config.get_section(section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool)

    connection = engine.connect()
    context.configure(
        connection=connection,
        target_metadata=db.Base.metadata,
        transaction_per_migration=True,
    )

    try:
        context.run_migrations()
    finally:
        connection.close()


configure_logging()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
