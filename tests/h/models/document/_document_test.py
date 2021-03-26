import logging
from unittest import mock

import pytest
import sqlalchemy as sa

from h import models
from h.models.document._document import (
    Document,
    merge_documents,
    update_document_metadata,
)
from h.models.document._exceptions import ConcurrentUpdateError


class TestDocumentFindByURIs:
    def test_with_one_matching_Document(self, db_session, factories):
        _noise = factories.Document(document_uris=[factories.DocumentURI()])

        matching_doc = factories.Document(
            document_uris=[factories.DocumentURI(), factories.DocumentURI()]
        )

        db_session.flush()

        actual = Document.find_by_uris(
            db_session,
            [
                "http://example.com/non-matching-noise",
                matching_doc.document_uris[1].uri,
            ],
        )

        assert actual.count() == 1
        assert actual.first() == matching_doc

    def test_no_matches(self, db_session, factories):
        _noise = factories.Document(document_uris=[factories.DocumentURI()])
        db_session.flush()

        actual = Document.find_by_uris(
            db_session, ["https://example.com/no_matching_document"]
        )
        assert actual.count() == 0


class TestDocumentFindOrCreateByURIs:
    def test_it_returns_a_document_when_theres_only_one(self, db_session, factories):
        # When searching with two URIs that match two DocumentURIs that both
        # point to the same Document, it should return that Document.
        doc_uri1 = factories.DocumentURI()
        doc_uri2 = factories.DocumentURI(document=doc_uri1.document)
        db_session.flush()

        actual = Document.find_or_create_by_uris(
            db_session, doc_uri1.uri, [doc_uri1.claimant, doc_uri2.claimant]
        )

        assert actual.count() == 1
        assert actual.first() == doc_uri1.document

    def test_with_no_existing_documents_we_create_one(self, db_session, factories):
        _noise = factories.DocumentURI()
        db_session.flush()

        documents = Document.find_or_create_by_uris(
            db_session,
            "https://en.wikipedia.org/wiki/Pluto",
            ["https://m.en.wikipedia.org/wiki/Pluto"],
        )

        assert documents.count() == 1

        actual = documents.first()
        assert isinstance(actual, Document)
        assert len(actual.document_uris) == 1

        doc_uri = actual.document_uris[0]
        assert doc_uri.claimant == "https://en.wikipedia.org/wiki/Pluto"
        assert doc_uri.uri == "https://en.wikipedia.org/wiki/Pluto"
        assert doc_uri.type == "self-claim"

    def test_raises_retryable_error_when_flush_fails(self, db_session, monkeypatch):
        def err():
            raise sa.exc.IntegrityError(None, None, None)

        monkeypatch.setattr(db_session, "flush", err)

        with pytest.raises(ConcurrentUpdateError):
            with db_session.no_autoflush:  # prevent premature IntegrityError
                Document.find_or_create_by_uris(
                    db_session,
                    "https://en.wikipedia.org/wiki/Pluto",
                    ["https://m.en.wikipedia.org/wiki/Pluto"],
                )


class TestDocumentWebURI:
    """Unit tests for Document.web_uri and Document.update_web_uri()."""

    def test_web_uri_is_initially_None(self, factories):
        assert factories.Document().web_uri is None

    @pytest.mark.parametrize(
        "document_uris,expected_web_uri",
        [
            # Given a single http or https URL it just uses it.
            ([("http://example.com", "self-claim")], "http://example.com"),
            ([("https://example.com", "self-claim")], "https://example.com"),
            ([("http://example.com", "rel-canonical")], "http://example.com"),
            ([("https://example.com", "rel-canonical")], "https://example.com"),
            ([("http://example.com", "rel-shortlink")], "http://example.com"),
            ([("https://example.com", "rel-shortlink")], "https://example.com"),
            # Given no http or https URLs it sets web_uri to None.
            ([], None),
            (
                [
                    ("ftp://example.com", "self-claim"),
                    ("android-app://example.com", "rel-canonical"),
                    ("urn:x-pdf:example", "rel-alternate"),
                    ("doi:http://example.com", "rel-shortlink"),
                ],
                None,
            ),
            # It prefers self-claim URLs over all other URLs.
            (
                [
                    ("https://example.com/shortlink", "rel-shortlink"),
                    ("https://example.com/canonical", "rel-canonical"),
                    ("https://example.com/self-claim", "self-claim"),
                ],
                "https://example.com/self-claim",
            ),
            # It prefers canonical URLs over all other non-self-claim URLs.
            (
                [
                    ("https://example.com/shortlink", "rel-shortlink"),
                    ("https://example.com/canonical", "rel-canonical"),
                ],
                "https://example.com/canonical",
            ),
            # If there's no self-claim or canonical URL it will return an https
            # URL of a different type.
            (
                [
                    ("ftp://example.com", "self-claim"),
                    ("urn:x-pdf:example", "rel-alternate"),
                    # This is the one that should be returned.
                    ("https://example.com/alternate", "rel-alternate"),
                    ("android-app://example.com", "rel-canonical"),
                    ("doi:http://example.com", "rel-shortlink"),
                ],
                "https://example.com/alternate",
            ),
            # If there's no self-claim or canonical URL it will return an http
            # URL of a different type.
            (
                [
                    ("ftp://example.com", "self-claim"),
                    ("urn:x-pdf:example", "rel-alternate"),
                    # This is the one that should be returned.
                    ("http://example.com/alternate", "rel-alternate"),
                    ("android-app://example.com", "rel-canonical"),
                    ("doi:http://example.com", "rel-shortlink"),
                ],
                "http://example.com/alternate",
            ),
        ],
    )
    def test_update_web_uri(self, document_uris, factories, expected_web_uri):
        document = factories.Document()

        for doc_uri_tuple in document_uris:
            factories.DocumentURI(
                uri=doc_uri_tuple[0], type=doc_uri_tuple[1], document=document
            )

        document.update_web_uri()

        assert document.web_uri == expected_web_uri


@pytest.mark.usefixtures("duplicate_docs")
class TestMergeDocuments:
    def test_it_returns_the_first_doc(self, db_session, duplicate_docs):
        merged = merge_documents(db_session, duplicate_docs)

        assert merged == duplicate_docs[0]

    def test_it_deletes_all_but_the_first(self, db_session, duplicate_docs):
        merge_documents(db_session, duplicate_docs)
        db_session.flush()

        count = (
            db_session.query(Document)
            .filter(Document.id.in_([duplicate_docs[1].id, duplicate_docs[2].id]))
            .count()
        )

        assert count == 0

    def test_it_moves_document_uris_to_the_first(self, db_session, duplicate_docs):
        merge_documents(db_session, duplicate_docs)
        db_session.flush()

        assert [len(doc.document_uris) for doc in duplicate_docs] == [3, 0, 0]

    def test_it_moves_document_meta_to_the_first(self, db_session, duplicate_docs):
        merge_documents(db_session, duplicate_docs)
        db_session.flush()

        assert [len(doc.meta) for doc in duplicate_docs] == [3, 0, 0]

    def test_it_moves_annotations_to_the_first(self, db_session, duplicate_docs):
        merge_documents(db_session, duplicate_docs)
        db_session.flush()

        for document, expected_count in zip(duplicate_docs, (3, 0, 0)):
            count = (
                db_session.query(models.Annotation)
                .filter_by(document_id=document.id)
                .count()
            )

            assert count == expected_count

    def test_it_raises_retryable_error_when_flush_fails(
        self, db_session, duplicate_docs, monkeypatch
    ):
        def err():
            raise sa.exc.IntegrityError(None, None, None)

        monkeypatch.setattr(db_session, "flush", err)

        with pytest.raises(ConcurrentUpdateError):
            merge_documents(db_session, duplicate_docs)

    def test_it_logs_when_its_called(self, caplog, db_session, duplicate_docs):
        caplog.set_level(logging.INFO)

        merge_documents(db_session, duplicate_docs)

        assert caplog.record_tuples == [
            ("h.models.document._document", 20, "Merging 3 documents")
        ]

    @pytest.fixture
    def duplicate_docs(self, db_session, factories):
        uri = "http://example.com/master"

        documents = []
        for _ in range(3):
            meta = factories.DocumentMeta()

            documents.append(
                factories.Document(
                    document_uris=[
                        factories.DocumentURI(claimant=meta.claimant, uri=uri)
                    ],
                    meta=[meta],
                )
            )

        db_session.flush()

        for doc in documents:
            db_session.add(models.Annotation(userid="userid", document_id=doc.id))

        return documents


class TestUpdateDocumentMetadata:
    def test_it_uses_the_target_uri_to_get_the_document(
        self, annotation, Document, mock_db_session, doc_uri_dicts
    ):
        update_document_metadata(
            mock_db_session,
            annotation.target_uri,
            [],
            doc_uri_dicts,
            annotation.created,
            annotation.updated,
        )

        Document.find_or_create_by_uris.assert_called_once_with(
            mock_db_session,
            annotation.target_uri,
            [data["uri"] for data in doc_uri_dicts],
            created=annotation.created,
            updated=annotation.updated,
        )

    def test_if_there_are_multiple_documents_it_merges_them_into_one(
        self, annotation, Document, merge_documents, mock_db_session
    ):
        Document.find_or_create_by_uris.return_value = mock.Mock(
            count=mock.Mock(return_value=3)
        )

        update_document_metadata(
            mock_db_session,
            annotation.target_uri,
            [],
            [],
            annotation.created,
            annotation.updated,
        )

        merge_documents.assert_called_once_with(
            mock_db_session,
            Document.find_or_create_by_uris.return_value,
            updated=annotation.updated,
        )

    def test_it_calls_first_document_found(self, annotation, mock_db_session, Document):
        Document.find_or_create_by_uris.return_value = mock.Mock(
            count=mock.Mock(return_value=1)
        )

        update_document_metadata(mock_db_session, annotation, [], [])

        Document.find_or_create_by_uris.return_value.first.assert_called_once_with()

    def test_it_updates_document_updated(
        self, annotation, Document, merge_documents, mock_db_session
    ):
        yesterday_ = "yesterday"
        document_ = merge_documents.return_value = mock.Mock(updated=yesterday_)
        Document.find_or_create_by_uris.return_value.first.return_value = document_

        update_document_metadata(
            mock_db_session,
            annotation.target_uri,
            [],
            [],
            annotation.created,
            annotation.updated,
        )

        assert document_.updated == annotation.updated

    def test_it_saves_all_the_document_uris(
        self,
        mock_db_session,
        annotation,
        Document,
        create_or_update_document_uri,
        doc_uri_dicts,
    ):
        Document.find_or_create_by_uris.return_value.count.return_value = 1

        update_document_metadata(
            mock_db_session,
            annotation.target_uri,
            [],
            doc_uri_dicts,
            annotation.created,
            annotation.updated,
        )

        assert create_or_update_document_uri.call_count == 3
        for doc_uri_dict in doc_uri_dicts:
            create_or_update_document_uri.assert_any_call(
                session=mock_db_session,
                document=Document.find_or_create_by_uris.return_value.first.return_value,
                created=annotation.created,
                updated=annotation.updated,
                **doc_uri_dict,
            )

    def test_it_updates_document_web_uri(
        self, annotation, Document, factories, mock_db_session
    ):
        document_ = mock.Mock(web_uri=None)
        Document.find_or_create_by_uris.return_value.count.return_value = 1
        Document.find_or_create_by_uris.return_value.first.return_value = document_

        update_document_metadata(
            mock_db_session,
            annotation.target_uri,
            [],
            [],
            annotation.created,
            annotation.updated,
        )

        document_.update_web_uri.assert_called_once_with()

    @pytest.fixture
    def doc_uri_dicts(self):
        return [
            {
                "uri": f"http://example.com/example_{i}",
                "claimant": "http://example.com/claimant",
                "type": "type",
                "content_type": None,
            }
            for i in range(3)
        ]

    def test_it_saves_all_the_document_metas(
        self, annotation, create_or_update_document_meta, Document, mock_db_session
    ):
        Document.find_or_create_by_uris.return_value.count.return_value = 1
        document_meta_dicts = [
            {
                "type": f"title_{i}",
                "value": f"value_{i}",
                "claimant": "http://example.com/claimant",
            }
            for i in range(3)
        ]

        update_document_metadata(
            mock_db_session,
            annotation.target_uri,
            document_meta_dicts,
            [],
            annotation.created,
            annotation.updated,
        )

        assert create_or_update_document_meta.call_count == 3
        for document_meta_dict in document_meta_dicts:
            create_or_update_document_meta.assert_any_call(
                session=mock_db_session,
                document=Document.find_or_create_by_uris.return_value.first.return_value,
                created=annotation.created,
                updated=annotation.updated,
                **document_meta_dict,
            )

    def test_it_returns_a_document(
        self, annotation, create_or_update_document_meta, Document, mock_db_session
    ):
        Document.find_or_create_by_uris.return_value.count.return_value = 1

        result = update_document_metadata(
            mock_db_session,
            annotation.target_uri,
            [],
            [],
            annotation.created,
            annotation.updated,
        )

        assert result == Document.find_or_create_by_uris.return_value.first.return_value

    @pytest.fixture
    def annotation(self):
        # We can't use the factories here because our factories use the methods
        # under test / being mocked here to create annotations
        return mock.Mock(spec=models.Annotation())

    @pytest.fixture
    def Document(self, patch):
        Document = patch("h.models.document._document.Document")
        Document.find_or_create_by_uris.return_value.count.return_value = 1
        return Document

    @pytest.fixture(autouse=True)
    def create_or_update_document_meta(self, patch):
        return patch("h.models.document._document.create_or_update_document_meta")

    @pytest.fixture(autouse=True)
    def create_or_update_document_uri(self, patch):
        return patch("h.models.document._document.create_or_update_document_uri")

    @pytest.fixture(autouse=True)
    def merge_documents(self, patch):
        return patch("h.models.document._document.merge_documents")
