from copy import copy
from enum import Enum

from sqlalchemy.event import listen
from sqlalchemy.orm.util import identity_key


class ObjectState(Enum):
    ADDED = "added"
    DELETED = "deleted"
    CHANGED = "changed"


class Tracker:
    """Observer which tracks whether a SQLAlchemy `Session` has uncommitted changes."""

    def __init__(self, session):
        self.session = session

        # Changes which have been flushed to the database (and thus not present
        # in `session.new`, `session.dirty` or `session.deleted) but have not
        # yet been _committed_.
        self._flushed_changes = {}

        listen(session, "after_flush", self._after_flush)
        listen(session, "after_commit", self._after_commit)
        listen(session, "after_rollback", self._after_rollback)

    def uncommitted_changes(self):
        """
        Return a list of changes to the `Session` which have not yet been _committed_ to the DB.

        The result is a list of (identity key, ObjectState) tuples.
        """
        changed = copy(self._flushed_changes)
        changed.update(self._unflushed_changes())

        return list(changed.items())

    def _unflushed_changes(self):
        """
        Return a map of changes which have not yet been flushed to the DB.

        In the context of the "after_flush" event handler, this returns changes
        which have just been flushed.

        If an object goes through multiple states in the same session (eg.
        added, then flushed, then changed) then only the last state for a given
        object is recorded.
        """
        changes = {}

        for obj in self.session.new:
            changes[identity_key(instance=obj)] = ObjectState.ADDED

        for obj in self.session.dirty:
            changes[identity_key(instance=obj)] = ObjectState.CHANGED

        for obj in self.session.deleted:
            changes[identity_key(instance=obj)] = ObjectState.DELETED

        return changes

    def _after_rollback(self, *args):  # pylint: disable=unused-argument
        self._flushed_changes = {}

    def _after_commit(self, *args):  # pylint: disable=unused-argument
        self._flushed_changes = {}

    def _after_flush(self, *args):  # pylint: disable=unused-argument
        self._flushed_changes.update(self._unflushed_changes())
