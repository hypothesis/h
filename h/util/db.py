# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sqlalchemy


def on_transaction_end(session):
    """
    Decorator for a function which should run after a top-level transaction ended.

    Transactions that are either implicitly or explicitly committed or rolled back will be
    closed at the end of a Pyramid view. This is here for cleaning up caches so that
    code after the view, exception views for example, will not be able to access
    detached instances.

    Example usage:

    .. code-block:: python

       @util.db.on_transaction_end(session)
       def flush_cache():
           self._cache = {}

    """
    def decorate(func):
        def _handler(_, transaction):
            # We only clear the cache when the top-level transaction finishes.
            if transaction.parent is None:
                func()

        sqlalchemy.event.listen(session, 'after_transaction_end', _handler)
        return func

    return decorate
