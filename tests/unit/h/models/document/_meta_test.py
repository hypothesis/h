from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest
import sqlalchemy as sa
from h_matchers import Any

from h.models import Document, DocumentMeta
from h.models.document import ConcurrentUpdateError, create_or_update_document_meta


class TestDocumentMeta:
    def test_repr(self):
        meta = DocumentMeta(id=1234)

        repr_string = repr(meta)

        assert "DocumentMet" in repr_string
        assert "1234" in repr_string


class TestCreateOrUpdateDocumentMeta:
    def test_it_creates_a_new_DocumentMeta_if_there_is_no_existing_one(
        self, db_session, meta_attrs
    ):
        # Add one non-matching DocumentMeta to the database to be ignored.
        db_session.add(DocumentMeta(**dict(meta_attrs, type="noise")))

        create_or_update_document_meta(session=db_session, **meta_attrs)

        document_meta = db_session.query(DocumentMeta).all()[-1]
        assert document_meta == Any.object.with_attrs(meta_attrs)

    @pytest.mark.parametrize("correct_document", (True, False))
    def test_it_updates_an_existing_DocumentMeta_if_there_is_one(
        self, db_session, meta_attrs, correct_document
    ):
        original_attrs = meta_attrs
        updated_attrs = dict(
            original_attrs,
            value="new value",
            # This should be ignored either way.
            document=meta_attrs["document"] if correct_document else Document(),
            created=datetime.now(),  # This should be ignored.
            updated=datetime.now(),
        )
        document_meta = DocumentMeta(**original_attrs)
        db_session.add(document_meta)

        create_or_update_document_meta(session=db_session, **updated_attrs)

        assert document_meta.value == updated_attrs["value"]
        assert document_meta.updated == updated_attrs["updated"]
        assert document_meta.created == original_attrs["created"]
        assert document_meta.document == original_attrs["document"]
        assert (
            len(db_session.query(DocumentMeta).all()) == 1
        ), "It shouldn't have added any new objects to the db"

    @pytest.mark.parametrize(
        "doc_title,final_title",
        ((None, "attr_title"), ("", "attr_title"), ("doc_title", "doc_title")),
    )
    def test_it_denormalizes_title_to_document_when_falsy(
        self, db_session, meta_attrs, doc_title, final_title
    ):
        meta_attrs["value"] = ["attr_title"]
        meta_attrs["document"] = document = Document(title=doc_title)

        db_session.add(document)

        create_or_update_document_meta(session=db_session, **meta_attrs)

        document = db_session.get(Document, document.id)
        assert document.title == final_title

    def test_it_logs_a_warning_with_existing_meta_on_a_different_doc(
        self, log, mock_db_session, factories, meta_attrs
    ):
        document_one = factories.Document()
        document_two = factories.Document()
        existing_document_meta = factories.DocumentMeta(document=document_one)
        mock_db_session.query.return_value.filter.return_value.one_or_none.return_value = (
            existing_document_meta
        )

        create_or_update_document_meta(
            session=mock_db_session, **dict(meta_attrs, document=document_two)
        )

        assert log.warning.call_count == 1

    def test_raises_retryable_error_when_flush_fails(
        self, db_session, monkeypatch, meta_attrs
    ):
        def err():
            raise sa.exc.IntegrityError(None, None, None)

        monkeypatch.setattr(db_session, "flush", err)

        with pytest.raises(ConcurrentUpdateError):
            with db_session.no_autoflush:  # prevent premature IntegrityError
                create_or_update_document_meta(session=db_session, **meta_attrs)

    @pytest.fixture
    def meta_attrs(self):
        return {
            "claimant": "http://example.com/claimant",
            "type": "title",
            "value": "the title",
            "document": Document(),
            "created": datetime.now() - timedelta(days=1),
            "updated": datetime.now(),
        }

    @pytest.fixture()
    def mock_db_session(self, db_session):
        return Mock(spec=db_session)

    @pytest.fixture
    def log(self, patch):
        return patch("h.models.document._meta.log")
