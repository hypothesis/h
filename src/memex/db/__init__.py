# -*- coding: utf-8 -*-

import logging

from sqlalchemy.ext.declarative import declarative_base

log = logging.getLogger(__name__)

#: The base class used by memex's models.
#:
#: This must be configured by the including application using
#: :py:func:`memex.db.set_base`.
Base = None


def init(engine, base=None, should_create=False, should_drop=False):
    """Initialise the database tables managed by `memex.db`."""
    if base is None:
        base = Base
    if should_drop:
        base.metadata.reflect(engine)
        base.metadata.drop_all(engine)
    if should_create:
        # In order to be able to generate UUIDs, we load the uuid-ossp
        # extension.
        engine.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
        base.metadata.create_all(engine)


def set_base(basecls=None):
    """Provide a base class for memex models."""
    global Base

    if basecls is None:
        if Base is None:
            log.info('model base class not already set, using defaults')
            Base = declarative_base()
        return

    Base = basecls
