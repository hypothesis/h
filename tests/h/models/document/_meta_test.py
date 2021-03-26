from datetime import datetime

import pytest
import sqlalchemy as sa

from h.models import Document, DocumentMeta
from h.models.document import ConcurrentUpdateError, create_or_update_document_meta
from tests.h.models.document.conftest import yesterday


class TestCreateOrUpdateDocumentMeta:
    def test_it_creates_a_new_DocumentMeta_if_there_is_no_existing_one(
        self, db_session
    ):
        claimant = "http://example.com/claimant"
        type_ = "title"
        value = "the title"
        document = Document()
        created = yesterday()
        updated = datetime.now()

        # Add one non-matching DocumentMeta to the database.
        # This should be ignored.
        db_session.add(
            DocumentMeta(
                claimant=claimant,
                # Different type means this should not match the query.
                type="different",
                value=value,
                document=document,
                created=created,
                updated=updated,
            )
        )

        create_or_update_document_meta(
            session=db_session,
            claimant=claimant,
            type=type_,
            value=value,
            document=document,
            created=created,
            updated=updated,
        )

        document_meta = db_session.query(DocumentMeta).all()[-1]
        assert document_meta.claimant == claimant
        assert document_meta.type == type_
        assert document_meta.value == value
        assert document_meta.document == document
        assert document_meta.created == created
        assert document_meta.updated == updated

    def test_it_updates_an_existing_DocumentMeta_if_there_is_one(self, db_session):
        claimant = "http://example.com/claimant"
        type_ = "title"
        value = "the title"
        document = Document()
        created = yesterday()
        updated = datetime.now()
        document_meta = DocumentMeta(
            claimant=claimant,
            type=type_,
            value=value,
            document=document,
            created=created,
            updated=updated,
        )
        db_session.add(document_meta)

        new_updated = datetime.now()
        create_or_update_document_meta(
            session=db_session,
            claimant=claimant,
            type=type_,
            value="new value",
            document=Document(),  # This should be ignored.
            created=datetime.now(),  # This should be ignored.
            updated=new_updated,
        )

        assert document_meta.value == "new value"
        assert document_meta.updated == new_updated
        assert document_meta.created == created, "It shouldn't update created"
        assert document_meta.document == document, "It shouldn't update document"
        assert (
            len(db_session.query(DocumentMeta).all()) == 1
        ), "It shouldn't have added any new objects to the db"

    def test_it_denormalizes_title_to_document_when_none(self, db_session):
        claimant = "http://example.com/claimant"
        type_ = "title"
        value = ["the title"]
        document = Document(title=None)
        created = yesterday()
        updated = datetime.now()
        db_session.add(document)

        create_or_update_document_meta(
            session=db_session,
            claimant=claimant,
            type=type_,
            value=value,
            document=document,
            created=created,
            updated=updated,
        )

        document = db_session.query(Document).get(document.id)
        assert document.title == value[0]

    def test_it_denormalizes_title_to_document_when_empty(self, db_session):
        claimant = "http://example.com/claimant"
        type_ = "title"
        value = ["the title"]
        document = Document(title="")
        created = yesterday()
        updated = datetime.now()
        db_session.add(document)

        create_or_update_document_meta(
            session=db_session,
            claimant=claimant,
            type=type_,
            value=value,
            document=document,
            created=created,
            updated=updated,
        )

        document = db_session.query(Document).get(document.id)
        assert document.title == value[0]

    def test_it_skips_denormalizing_title_to_document_when_already_set(
        self, db_session
    ):
        claimant = "http://example.com/claimant"
        type_ = "title"
        value = ["the title"]
        document = Document(title="foobar")
        created = yesterday()
        updated = datetime.now()
        db_session.add(document)

        create_or_update_document_meta(
            session=db_session,
            claimant=claimant,
            type=type_,
            value=value,
            document=document,
            created=created,
            updated=updated,
        )

        document = db_session.query(Document).get(document.id)
        assert document.title == "foobar"

    def test_it_logs_a_warning(self, log, mock_db_session, factories):
        """
        It should warn on document mismatches.

        It should warn if there's an existing DocumentMeta with a different
        Document.
        """
        document_one = factories.Document()
        document_two = factories.Document()
        existing_document_meta = factories.DocumentMeta(document=document_one)

        mock_db_session.query.return_value.filter.return_value.one_or_none.return_value = (
            existing_document_meta
        )

        create_or_update_document_meta(
            session=mock_db_session,
            claimant="http://example.com/claimant",
            type="title",
            value="new value",
            document=document_two,
            created=yesterday(),
            updated=datetime.now(),
        )

        assert log.warning.call_count == 1

    def test_raises_retryable_error_when_flush_fails(self, db_session, monkeypatch):
        document = Document()

        def err():
            raise sa.exc.IntegrityError(None, None, None)

        monkeypatch.setattr(db_session, "flush", err)

        with pytest.raises(ConcurrentUpdateError):
            with db_session.no_autoflush:  # prevent premature IntegrityError
                create_or_update_document_meta(
                    session=db_session,
                    claimant="http://example.com",
                    type="title",
                    value="My Title",
                    document=document,
                    created=datetime.now(),
                    updated=datetime.now(),
                )

    @pytest.fixture
    def log(self, patch):
        return patch("h.models.document._meta.log")
