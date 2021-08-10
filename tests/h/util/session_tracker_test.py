from uuid import uuid4

import pytest
from sqlalchemy.orm.util import identity_key

from h.db.types import _get_urlsafe_from_hex
from h.models import Annotation, Document
from h.util.session_tracker import ObjectState, Tracker


def generate_ann_id():
    """Generate a random annotation identifier in the encoded form used by the API."""
    return _get_urlsafe_from_hex(str(uuid4()))


class TestTracker:
    @pytest.mark.usefixtures("session")
    def test_uncommitted_changes_returns_unflushed_changes(
        self, tracker, expected_changes
    ):
        added_entry, changed_entry, deleted_entry = expected_changes

        changes = tracker.uncommitted_changes()

        assert added_entry in changes
        assert changed_entry in changes
        assert deleted_entry in changes

    def test_uncommitted_changes_returns_flushed_changes(
        self, tracker, session, expected_changes
    ):
        added_entry, changed_entry, deleted_entry = expected_changes

        session.flush()
        changes = tracker.uncommitted_changes()

        assert added_entry in changes
        assert changed_entry in changes
        assert deleted_entry in changes

    def test_uncommitted_changes_does_not_return_committed_changes(
        self, tracker, session
    ):
        session.commit()
        assert tracker.uncommitted_changes() == []

    def test_uncommitted_changes_does_not_return_rolled_back_changes(
        self, tracker, session
    ):
        session.rollback()
        assert tracker.uncommitted_changes() == []

    @pytest.fixture
    def expected_changes(self, added_ann_id, changed_ann_id, deleted_ann_id):
        added_entry = (identity_key(Annotation, (added_ann_id,)), ObjectState.ADDED)
        changed_entry = (
            identity_key(Annotation, (changed_ann_id,)),
            ObjectState.CHANGED,
        )
        deleted_entry = (
            identity_key(Annotation, (deleted_ann_id,)),
            ObjectState.DELETED,
        )

        return (added_entry, changed_entry, deleted_entry)

    @pytest.fixture
    def added_ann_id(self):
        return generate_ann_id()

    @pytest.fixture
    def changed_ann_id(self):
        return generate_ann_id()

    @pytest.fixture
    def deleted_ann_id(self):
        return generate_ann_id()

    @pytest.fixture
    def session(self, db_session, added_ann_id, changed_ann_id, deleted_ann_id):
        # Populate the DB session with different types of change relative to the
        # last-committed state. We could use any model object for this purpose
        # but annotations are the primary object in the system.

        doc = Document(web_uri="https://example.org")
        changed = Annotation(
            id=changed_ann_id, userid="foo", groupid="wibble", document=doc
        )
        deleted = Annotation(
            id=deleted_ann_id, userid="foo", groupid="wibble", document=doc
        )
        db_session.add(changed)
        db_session.add(deleted)
        db_session.commit()

        changed.text = "changed text"
        db_session.delete(deleted)

        added = Annotation(
            id=added_ann_id, userid="foo", groupid="wibble", document=doc
        )
        db_session.add(added)

        return db_session

    @pytest.fixture
    def tracker(self, db_session):
        return Tracker(db_session)
