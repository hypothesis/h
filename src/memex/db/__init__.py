# -*- coding: utf-8 -*-

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
        base.metadata.drop_all(engine)
    if should_create:
        # In order to be able to generate UUIDs, we load the uuid-ossp
        # extension.
        engine.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
        base.metadata.create_all(engine)


def set_base(basecls):
    """Provide a base class for memex models."""
    global Base
    Base = basecls
