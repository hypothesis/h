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
from h.models.document._meta import DocumentMeta
from h.models.document._uri import DocumentURI


class TestDocumentFindByURIs:
    def test_with_one_matching_Document(self, db_session):
        # One Document with a non-matching DocumentURI pointing to it.
        # find_by_uris() should not return this Document.
        document1 = Document()
        uri1 = "https://de.wikipedia.org/wiki/Hauptseite"
        document1.document_uris.append(DocumentURI(claimant=uri1, uri=uri1))

        # A second Document with one matching and one non-matching DocumentURI
        # pointing to it. find_by_uris() should return this Document.
        document2 = Document()
        uri2 = "https://en.wikipedia.org/wiki/Main_Page"
        document2.document_uris.append(DocumentURI(claimant=uri2, uri=uri2))
        uri3 = "https://en.wikipedia.org"
        document2.document_uris.append(DocumentURI(claimant=uri3, uri=uri2))

        db_session.add_all([document1, document2])
        db_session.flush()

        actual = Document.find_by_uris(
            db_session,
            [
                "https://en.wikipedia.org/wiki/Main_Page",
                "https://m.en.wikipedia.org/wiki/Main_Page",
            ],
        )

        assert actual.count() == 1
        assert actual.first() == document2

    def test_no_matches(self, db_session):
        document = Document()
        document.document_uris.append(
            DocumentURI(
                claimant="https://en.wikipedia.org/wiki/Main_Page",
                uri="https://en.wikipedia.org/wiki/Main_Page",
            )
        )
        db_session.add(document)
        db_session.flush()

        actual = Document.find_by_uris(
            db_session, ["https://de.wikipedia.org/wiki/Hauptseite"]
        )
        assert actual.count() == 0


class TestDocumentFindOrCreateByURIs:
    def test_with_one_existing_Document(self, db_session):
        """
        When there's one matching Document it should return that Document.

        When searching with two URIs that match two DocumentURIs that both
        point to the same Document, it should return that Document.

        """
        document = Document()
        docuri1 = DocumentURI(
            claimant="https://en.wikipedia.org/wiki/Main_Page",
            uri="https://en.wikipedia.org/wiki/Main_Page",
            document=document,
        )
        docuri2 = DocumentURI(
            claimant="https://en.wikipedia.org/wiki/http/en.m.wikipedia.org/wiki/Main_Page",
            uri="https://en.wikipedia.org/wiki/Main_Page",
            document=document,
        )

        db_session.add(docuri1)
        db_session.add(docuri2)
        db_session.flush()

        actual = Document.find_or_create_by_uris(
            db_session,
            "https://en.wikipedia.org/wiki/Main_Page",
            [
                "https://en.wikipedia.org/wiki/http/en.m.wikipedia.org/wiki/Main_Page",
                "https://m.en.wikipedia.org/wiki/Main_Page",
            ],
        )

        assert actual.count() == 1
        assert actual.first() == document

    def test_with_no_existing_documents(self, db_session):
        """When there are no matching Documents it creates and returns one."""
        document = Document()
        docuri = DocumentURI(
            claimant="https://en.wikipedia.org/wiki/Main_Page",
            uri="https://en.wikipedia.org/wiki/Main_Page",
            document=document,
        )

        db_session.add(docuri)
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

        docuri = actual.document_uris[0]
        assert docuri.claimant == "https://en.wikipedia.org/wiki/Pluto"
        assert docuri.uri == "https://en.wikipedia.org/wiki/Pluto"
        assert docuri.type == "self-claim"

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

        for docuri_tuple in document_uris:
            factories.DocumentURI(
                uri=docuri_tuple[0], type=docuri_tuple[1], document=document
            )

        document.update_web_uri()

        assert document.web_uri == expected_web_uri


@pytest.mark.usefixtures("merge_data")
class TestMergeDocuments:
    def test_merge_documents_returns_master(self, db_session, merge_data):
        master, _, _ = merge_data

        merged_master = merge_documents(db_session, merge_data)

        assert merged_master == master

    def test_merge_documents_deletes_duplicate_documents(self, db_session, merge_data):
        _, duplicate_1, duplicate_2 = merge_data

        merge_documents(db_session, merge_data)
        db_session.flush()

        count = (
            db_session.query(Document)
            .filter(Document.id.in_([duplicate_1.id, duplicate_2.id]))
            .count()
        )

        assert count == 0

    def test_merge_documents_rewires_document_uris(self, db_session, merge_data):
        master, duplicate_1, duplicate_2 = merge_data

        merge_documents(db_session, merge_data)
        db_session.flush()

        assert len(master.document_uris) == 3
        assert len(duplicate_1.document_uris) == 0
        assert len(duplicate_2.document_uris) == 0

    def test_merge_documents_rewires_document_meta(self, db_session, merge_data):
        master, duplicate_1, duplicate_2 = merge_data

        merge_documents(db_session, merge_data)
        db_session.flush()

        assert len(master.meta) == 3
        assert len(duplicate_1.meta) == 0
        assert len(duplicate_2.meta) == 0

    def test_merge_documents_rewires_annotations(self, db_session, merge_data):
        master, duplicate_1, duplicate_2 = merge_data

        merge_documents(db_session, merge_data)
        db_session.flush()

        assert (
            6
            == db_session.query(models.Annotation)
            .filter_by(document_id=master.id)
            .count()
        )
        assert (
            0
            == db_session.query(models.Annotation)
            .filter_by(document_id=duplicate_1.id)
            .count()
        )
        assert (
            0
            == db_session.query(models.Annotation)
            .filter_by(document_id=duplicate_2.id)
            .count()
        )

    def test_raises_retryable_error_when_flush_fails(
        self, db_session, merge_data, monkeypatch
    ):
        def err():
            raise sa.exc.IntegrityError(None, None, None)

        monkeypatch.setattr(db_session, "flush", err)

        with pytest.raises(ConcurrentUpdateError):
            merge_documents(db_session, merge_data)

    def test_merge_documents_logs_when_its_called(self, caplog, db_session, merge_data):
        caplog.set_level(logging.INFO)

        merge_documents(db_session, merge_data)

        assert caplog.record_tuples == [
            ("h.models.document._document", 20, "Merging 3 documents")
        ]

    @pytest.fixture
    def merge_data(self, db_session, request):
        master = Document(
            document_uris=[
                DocumentURI(
                    claimant="https://en.wikipedia.org/wiki/Main_Page",
                    uri="https://en.wikipedia.org/wiki/Main_Page",
                    type="self-claim",
                )
            ],
            meta=[
                DocumentMeta(
                    claimant="https://en.wikipedia.org/wiki/Main_Page",
                    type="title",
                    value="Wikipedia, the free encyclopedia",
                )
            ],
        )
        duplicate_1 = Document(
            document_uris=[
                DocumentURI(
                    claimant="https://m.en.wikipedia.org/wiki/Main_Page",
                    uri="https://en.wikipedia.org/wiki/Main_Page",
                    type="rel-canonical",
                )
            ],
            meta=[
                DocumentMeta(
                    claimant="https://m.en.wikipedia.org/wiki/Main_Page",
                    type="title",
                    value="Wikipedia, the free encyclopedia",
                )
            ],
        )
        duplicate_2 = Document(
            document_uris=[
                DocumentURI(
                    claimant="https://en.wikipedia.org/wiki/Home",
                    uri="https://en.wikipedia.org/wiki/Main_Page",
                    type="rel-canonical",
                )
            ],
            meta=[
                DocumentMeta(
                    claimant="https://en.wikipedia.org/wiki/Home",
                    type="title",
                    value="Wikipedia, the free encyclopedia",
                )
            ],
        )

        db_session.add_all([master, duplicate_1, duplicate_2])
        db_session.flush()

        master_ann_1 = models.Annotation(userid="luke", document_id=master.id)
        master_ann_2 = models.Annotation(userid="alice", document_id=master.id)
        duplicate_1_ann_1 = models.Annotation(userid="lucy", document_id=duplicate_1.id)
        duplicate_1_ann_2 = models.Annotation(userid="bob", document_id=duplicate_1.id)
        duplicate_2_ann_1 = models.Annotation(userid="amy", document_id=duplicate_2.id)
        duplicate_2_ann_2 = models.Annotation(userid="dan", document_id=duplicate_2.id)
        db_session.add_all(
            [
                master_ann_1,
                master_ann_2,
                duplicate_1_ann_1,
                duplicate_1_ann_2,
                duplicate_2_ann_1,
                duplicate_2_ann_2,
            ]
        )
        return (master, duplicate_1, duplicate_2)


class TestUpdateDocumentMetadata:
    def test_it_uses_the_target_uri_to_get_the_document(
        self, annotation, Document, session
    ):
        document_uri_dicts = [
            {
                "uri": "http://example.com/example_1",
                "claimant": "http://example.com/claimant",
                "type": "type",
                "content_type": None,
            },
            {
                "uri": "http://example.com/example_2",
                "claimant": "http://example.com/claimant",
                "type": "type",
                "content_type": None,
            },
            {
                "uri": "http://example.com/example_3",
                "claimant": "http://example.com/claimant",
                "type": "type",
                "content_type": None,
            },
        ]

        update_document_metadata(
            session,
            annotation.target_uri,
            [],
            document_uri_dicts,
            annotation.created,
            annotation.updated,
        )

        Document.find_or_create_by_uris.assert_called_once_with(
            session,
            annotation.target_uri,
            [
                "http://example.com/example_1",
                "http://example.com/example_2",
                "http://example.com/example_3",
            ],
            created=annotation.created,
            updated=annotation.updated,
        )

    def test_if_there_are_multiple_documents_it_merges_them_into_one(
        self, annotation, Document, merge_documents, session
    ):
        """If it finds more than one document it calls merge_documents()."""
        Document.find_or_create_by_uris.return_value = mock.Mock(
            count=mock.Mock(return_value=3)
        )

        update_document_metadata(
            session,
            annotation.target_uri,
            [],
            [],
            annotation.created,
            annotation.updated,
        )

        merge_documents.assert_called_once_with(
            session,
            Document.find_or_create_by_uris.return_value,
            updated=annotation.updated,
        )

    def test_it_calls_first(self, annotation, session, Document):
        """If it finds only one document it calls first()."""
        Document.find_or_create_by_uris.return_value = mock.Mock(
            count=mock.Mock(return_value=1)
        )

        update_document_metadata(session, annotation, [], [])

        Document.find_or_create_by_uris.return_value.first.assert_called_once_with()

    def test_it_updates_document_updated(
        self, annotation, Document, merge_documents, session
    ):
        yesterday_ = "yesterday"
        document_ = merge_documents.return_value = mock.Mock(updated=yesterday_)
        Document.find_or_create_by_uris.return_value.first.return_value = document_

        update_document_metadata(
            session,
            annotation.target_uri,
            [],
            [],
            annotation.created,
            annotation.updated,
        )

        assert document_.updated == annotation.updated

    def test_it_saves_all_the_document_uris(
        self, session, annotation, Document, create_or_update_document_uri
    ):
        """It creates or updates a DocumentURI for each document URI dict."""
        Document.find_or_create_by_uris.return_value.count.return_value = 1

        document_uri_dicts = [
            {
                "uri": "http://example.com/example_1",
                "claimant": "http://example.com/claimant",
                "type": "type",
                "content_type": None,
            },
            {
                "uri": "http://example.com/example_2",
                "claimant": "http://example.com/claimant",
                "type": "type",
                "content_type": None,
            },
            {
                "uri": "http://example.com/example_3",
                "claimant": "http://example.com/claimant",
                "type": "type",
                "content_type": None,
            },
        ]

        update_document_metadata(
            session,
            annotation.target_uri,
            [],
            document_uri_dicts,
            annotation.created,
            annotation.updated,
        )

        assert create_or_update_document_uri.call_count == 3
        for doc_uri_dict in document_uri_dicts:
            create_or_update_document_uri.assert_any_call(
                session=session,
                document=Document.find_or_create_by_uris.return_value.first.return_value,
                created=annotation.created,
                updated=annotation.updated,
                **doc_uri_dict
            )

    def test_it_updates_document_web_uri(
        self, annotation, Document, factories, session
    ):
        document_ = mock.Mock(web_uri=None)
        Document.find_or_create_by_uris.return_value.count.return_value = 1
        Document.find_or_create_by_uris.return_value.first.return_value = document_

        update_document_metadata(
            session,
            annotation.target_uri,
            [],
            [],
            annotation.created,
            annotation.updated,
        )

        document_.update_web_uri.assert_called_once_with()

    def test_it_saves_all_the_document_metas(
        self, annotation, create_or_update_document_meta, Document, session
    ):
        """It creates or updates a DocumentMeta for each document meta dict."""
        Document.find_or_create_by_uris.return_value.count.return_value = 1

        document_meta_dicts = [
            {
                "claimant": "http://example.com/claimant",
                "type": "title",
                "value": "foo",
            },
            {
                "type": "article title",
                "value": "bar",
                "claimant": "http://example.com/claimant",
            },
            {
                "type": "site title",
                "value": "gar",
                "claimant": "http://example.com/claimant",
            },
        ]

        update_document_metadata(
            session,
            annotation.target_uri,
            document_meta_dicts,
            [],
            annotation.created,
            annotation.updated,
        )

        assert create_or_update_document_meta.call_count == 3
        for document_meta_dict in document_meta_dicts:
            create_or_update_document_meta.assert_any_call(
                session=session,
                document=Document.find_or_create_by_uris.return_value.first.return_value,
                created=annotation.created,
                updated=annotation.updated,
                **document_meta_dict
            )

    def test_it_returns_a_document(
        self, annotation, create_or_update_document_meta, Document, session
    ):
        Document.find_or_create_by_uris.return_value.count.return_value = 1

        result = update_document_metadata(
            session,
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

    @pytest.fixture
    def session(self, db_session):
        return mock.Mock(spec=db_session)
