from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest
import sqlalchemy as sa
from h_matchers import Any

from h.models.document import ConcurrentUpdateError, create_or_update_document_uri
from h.models.document._document import Document
from h.models.document._uri import DocumentURI


class TestDocumentURI:
    def test_it_normalizes_the_uri(self):
        document_uri = DocumentURI(uri="http://example.com/")

        assert (
            document_uri.uri_normalized  # pylint:disable=comparison-with-callable
            == "httpx://example.com"
        )

    def test_type_defaults_to_empty_string(self, db_session, document_uri, factories):
        document_uri = factories.DocumentURI(type=None)
        db_session.flush()

        assert not document_uri.type

    def test_you_cannot_set_type_to_null(self, db_session, document_uri):
        document_uri.type = None

        with pytest.raises(sa.exc.IntegrityError):
            db_session.flush()

    def test_content_type_defaults_to_empty_string(self, db_session, factories):
        document_uri = factories.DocumentURI(content_type=None)
        db_session.flush()

        assert not document_uri.content_type

    def test_you_cannot_set_content_type_to_null(self, db_session, document_uri):
        document_uri.content_type = None

        with pytest.raises(sa.exc.IntegrityError):
            db_session.flush()

    def test_you_cannot_add_duplicate_document_uris(self, db_session):
        # You can't add DocumentURI's with the same claimant, uri, type and
        # content_type, even if they have different documents.
        attrs = {
            "claimant": "http://www.example.com",
            "uri": "http://www.example.com",
            "type": "foo",
            "content_type": "bar",
        }

        db_session.add(DocumentURI(**attrs, document=Document()))
        db_session.add(DocumentURI(**attrs, document=Document()))

        with pytest.raises(sa.exc.IntegrityError):
            db_session.commit()

    def test_repr(self):
        uri = DocumentURI(id=1234)

        repr_string = repr(uri)

        assert "DocumentURI" in repr_string
        assert "1234" in repr_string

    @pytest.fixture
    def document_uri(self, db_session, factories):
        document_uri = factories.DocumentURI()
        db_session.flush()
        return document_uri


@pytest.mark.usefixtures("log")
class TestCreateOrUpdateDocumentURI:
    def test_it_updates_the_existing_DocumentURI_if_there_is_one(
        self, db_session, doc_uri_attrs
    ):
        original_attrs = doc_uri_attrs
        updated_attrs = dict(
            original_attrs, created=datetime.now(), updated=datetime.now()
        )
        document_uri = DocumentURI(**original_attrs)
        db_session.add(document_uri)

        create_or_update_document_uri(session=db_session, **updated_attrs)

        assert document_uri.created == original_attrs["created"]
        assert document_uri.updated == updated_attrs["updated"]
        assert (
            len(db_session.query(DocumentURI).all()) == 1
        ), "It shouldn't have added any new objects to the db"

    def test_it_creates_a_new_DocumentURI_if_there_is_no_existing_one(
        self, db_session, doc_uri_attrs
    ):
        original_attrs = doc_uri_attrs
        updated_attrs = dict(
            original_attrs, created=datetime.now(), updated=datetime.now()
        )
        # Add one non-matching DocumentURI to the database.
        db_session.add(DocumentURI(**dict(original_attrs, content_type="different")))

        create_or_update_document_uri(session=db_session, **updated_attrs)

        document_uri = (
            db_session.query(DocumentURI).order_by(DocumentURI.created.desc()).first()
        )
        assert document_uri == Any.object.with_attrs(updated_attrs)

    def test_it_skips_denormalizing_http_uris_to_document(
        self, db_session, doc_uri_attrs
    ):
        doc_uri_attrs["document"] = document = Document(
            web_uri="http://example.com/first_uri.html"
        )
        db_session.add(document)

        create_or_update_document_uri(session=db_session, **doc_uri_attrs)

        document_ = db_session.query(Document).get(document.id)
        assert document_.web_uri == "http://example.com/first_uri.html"

    def test_it_logs_a_warning_if_document_ids_differ(
        self, log, mock_db_session, factories, doc_uri_attrs
    ):
        # Ensure the document we use, and that returned by filter first are
        # different
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            factories.DocumentURI()
        )
        different_document = factories.Document()

        create_or_update_document_uri(
            session=mock_db_session, **dict(doc_uri_attrs, document=different_document)
        )

        assert log.warning.call_count == 1

    def test_raises_retryable_error_when_flush_fails(
        self, db_session, monkeypatch, doc_uri_attrs
    ):
        def err():
            raise sa.exc.IntegrityError(None, None, None)

        monkeypatch.setattr(db_session, "flush", err)

        with pytest.raises(ConcurrentUpdateError):
            with db_session.no_autoflush:  # prevent premature IntegrityError
                create_or_update_document_uri(session=db_session, **doc_uri_attrs)

    @pytest.fixture
    def doc_uri_attrs(self):
        return {
            "claimant": "http://example.com/example_claimant.html",
            "uri": "http://example.com/example_uri.html",
            "type": "self-claim",
            "content_type": "",
            "document": Document(),
            "created": datetime.now() - timedelta(days=1),
            "updated": datetime.now() - timedelta(days=1),
        }

    @pytest.fixture()
    def mock_db_session(self, db_session):
        return Mock(spec=db_session)

    @pytest.fixture
    def log(self, patch):
        return patch("h.models.document._uri.log")
