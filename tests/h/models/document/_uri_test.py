from datetime import datetime

import pytest
import sqlalchemy as sa

from h.models.document import ConcurrentUpdateError, create_or_update_document_uri
from h.models.document._document import Document
from h.models.document._uri import DocumentURI
from tests.h.models.document.conftest import yesterday


class TestDocumentURI:
    def test_it_normalizes_the_uri(self):
        document_uri = DocumentURI(uri="http://example.com/")

        assert document_uri.uri_normalized == "httpx://example.com"

    def test_type_defaults_to_empty_string(self, db_session):
        document_uri = DocumentURI(
            claimant="http://www.example.com",
            uri="http://www.example.com",
            type=None,
            content_type="bar",
            document=Document(),
        )
        db_session.add(document_uri)

        db_session.flush()

        assert document_uri.type == ""

    def test_you_cannot_set_type_to_null(self, db_session):
        document_uri = DocumentURI(
            claimant="http://www.example.com",
            uri="http://www.example.com",
            type="foo",
            content_type="bar",
            document=Document(),
        )
        db_session.add(document_uri)
        db_session.flush()

        document_uri.type = None

        with pytest.raises(sa.exc.IntegrityError):
            db_session.flush()

    def test_content_type_defaults_to_empty_string(self, db_session):
        document_uri = DocumentURI(
            claimant="http://www.example.com",
            uri="http://www.example.com",
            type="bar",
            content_type=None,
            document=Document(),
        )
        db_session.add(document_uri)

        db_session.flush()

        assert document_uri.content_type == ""

    def test_you_cannot_set_content_type_to_null(self, db_session):
        document_uri = DocumentURI(
            claimant="http://www.example.com",
            uri="http://www.example.com",
            type="foo",
            content_type="bar",
            document=Document(),
        )
        db_session.add(document_uri)
        db_session.flush()

        document_uri.content_type = None

        with pytest.raises(sa.exc.IntegrityError):
            db_session.flush()

    def test_you_cannot_add_duplicate_document_uris(self, db_session):
        """
        You can't add duplicate DocumentURI's to the database.

        You can't add DocumentURI's with the same claimant, uri, type and
        content_type, even if they have different documents.

        """
        db_session.add_all(
            [
                DocumentURI(
                    claimant="http://www.example.com",
                    uri="http://www.example.com",
                    type="foo",
                    content_type="bar",
                    document=Document(),
                ),
                DocumentURI(
                    claimant="http://www.example.com",
                    uri="http://www.example.com",
                    type="foo",
                    content_type="bar",
                    document=Document(),
                ),
            ]
        )

        with pytest.raises(sa.exc.IntegrityError):
            db_session.commit()


@pytest.mark.usefixtures("log")
class TestCreateOrUpdateDocumentURI:
    def test_it_updates_the_existing_DocumentURI_if_there_is_one(self, db_session):
        claimant = "http://example.com/example_claimant.html"
        uri = "http://example.com/example_uri.html"
        type_ = "self-claim"
        content_type = ""
        document_ = Document()
        created = yesterday()
        updated = yesterday()
        document_uri = DocumentURI(
            claimant=claimant,
            uri=uri,
            type=type_,
            content_type=content_type,
            document=document_,
            created=created,
            updated=updated,
        )
        db_session.add(document_uri)

        now_ = datetime.now()
        create_or_update_document_uri(
            session=db_session,
            claimant=claimant,
            uri=uri,
            type=type_,
            content_type=content_type,
            document=document_,
            created=now_,
            updated=now_,
        )

        assert document_uri.created == created
        assert document_uri.updated == now_
        assert (
            len(db_session.query(DocumentURI).all()) == 1
        ), "It shouldn't have added any new objects to the db"

    def test_it_creates_a_new_DocumentURI_if_there_is_no_existing_one(self, db_session):
        claimant = "http://example.com/example_claimant.html"
        uri = "http://example.com/example_uri.html"
        type_ = "self-claim"
        content_type = ""
        document_ = Document()
        created = yesterday()
        updated = yesterday()

        # Add one non-matching DocumentURI to the database.
        db_session.add(
            DocumentURI(
                claimant=claimant,
                uri=uri,
                type=type_,
                # Different content_type means this DocumentURI should not match
                # the query.
                content_type="different",
                document=document_,
                created=created,
                updated=updated,
            )
        )

        create_or_update_document_uri(
            session=db_session,
            claimant=claimant,
            uri=uri,
            type=type_,
            content_type=content_type,
            document=document_,
            created=datetime.now(),
            updated=datetime.now(),
        )

        document_uri = (
            db_session.query(DocumentURI).order_by(DocumentURI.created.desc()).first()
        )
        assert document_uri.claimant == claimant
        assert document_uri.uri == uri
        assert document_uri.type == type_
        assert document_uri.content_type == content_type
        assert document_uri.document == document_
        assert document_uri.created > created
        assert document_uri.updated > updated

    def test_it_skips_denormalizing_http_s_uri_to_document(self, db_session):
        document_ = Document(web_uri="http://example.com/first_uri.html")
        db_session.add(document_)

        create_or_update_document_uri(
            session=db_session,
            claimant="http://example.com/example_claimant.html",
            uri="http://example.com/second_uri.html",
            type="self-claim",
            content_type="",
            document=document_,
            created=datetime.now(),
            updated=datetime.now(),
        )

        document_ = db_session.query(Document).get(document_.id)
        assert document_.web_uri == "http://example.com/first_uri.html"

    def test_it_logs_a_warning_if_document_ids_differ(
        self, log, mock_db_session, factories
    ):
        """
        It should log a warning on Document objects mismatch.

        If there's an existing DocumentURI and its .document property is
        different to the given document it shoulg log a warning.

        """

        # existing_document_uri.document won't be equal to the given document.

        existing_document_uri = factories.DocumentURI()
        different_document = factories.Document()
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            existing_document_uri
        )

        create_or_update_document_uri(
            session=mock_db_session,
            claimant="http://example.com/example_claimant.html",
            uri="http://example.com/example_uri.html",
            type="self-claim",
            content_type=None,
            document=different_document,
            created=datetime.now(),
            updated=datetime.now(),
        )

        assert log.warning.call_count == 1

    def test_raises_retryable_error_when_flush_fails(self, db_session, monkeypatch):
        document_ = Document()

        def err():
            raise sa.exc.IntegrityError(None, None, None)

        monkeypatch.setattr(db_session, "flush", err)

        with pytest.raises(ConcurrentUpdateError):
            with db_session.no_autoflush:  # prevent premature IntegrityError
                create_or_update_document_uri(
                    session=db_session,
                    claimant="http://example.com",
                    uri="http://example.org",
                    type="rel-canonical",
                    content_type="text/html",
                    document=document_,
                    created=datetime.now(),
                    updated=datetime.now(),
                )

    @pytest.fixture
    def log(self, patch):
        return patch("h.models.document._uri.log")
