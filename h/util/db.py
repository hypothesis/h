# -*- coding: utf-8 -*-

from __future__ import unicode_literals

try:
    from functools import lru_cache
except ImportError:
    from backports.functools_lru_cache import lru_cache

import sqlalchemy


class lru_cache_in_transaction(object):  # noqa: N801
    """
    Decorator to wrap a function with a memoizing callable that saves up to
    the `maxsize` most recent calls. The underlying cache is automatically
    cleared at the end of the database transaction.

    Since a dictionary is used to cache results, the positional and keyword
    arguments to the function must be hashable.

    For documentation of the `maxsize` and `typed` arguments, see the
    documentation of :py:func:`functools.lru_cache`.

    Example::

        @lru_cache_in_transaction(session)
        def fetch_user(userid):
            return session.query(models.User).filter_by(userid=userid).one_or_none()

        fetch_user('acct:foo@example.com')  # => executes a query
        fetch_user('acct:foo@example.com')  # => returns cached value
        fetch_user('acct:bar@example.com')  # => executes a query

        session.commit()

        fetch_user('acct:foo@example.com')  # => executes a query
    """

    def __init__(self, session, maxsize=128, typed=False):
        self._session = session
        self._maxsize = maxsize
        self._typed = typed

    def __call__(self, func):
        decorator = lru_cache(maxsize=self._maxsize, typed=self._typed)
        wrapped = decorator(func)
        on_transaction_end(self._session)(wrapped.cache_clear)
        return wrapped


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
