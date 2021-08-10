import functools
import logging
from datetime import datetime as _datetime
from unittest.mock import sentinel

import pytest
import sqlalchemy as sa

from h import models
from h.models.document._document import (
    Document,
    merge_documents,
    update_document_metadata,
)
from h.models.document._exceptions import ConcurrentUpdateError


class TestDocument:
    def test_repr(self):
        document = Document(id=1234)

        repr_string = repr(document)

        assert "Document" in repr_string
        assert "1234" in repr_string


class TestDocumentFindByURIs:
    def test_with_one_matching_Document(self, db_session, factories):
        factories.Document(document_uris=[factories.DocumentURI()])  # Noise

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
        factories.Document(document_uris=[factories.DocumentURI()])  # Noise
        db_session.flush()

        actual = Document.find_by_uris(
            db_session, ["https://example.com/no_matching_document"]
        )
        assert not actual.count()


class TestDocumentFindOrCreateByURIs:
    def test_it_returns_a_document_when_theres_only_one(self, db_session, factories):
        # When searching with two URIs that match two DocumentURIs that both
        # point to the same Document, it should return that Document.
        doc_uri1 = factories.DocumentURI()
        doc_uri2 = factories.DocumentURI(document=doc_uri1.document)
        db_session.flush()

        actual = Document.find_or_create_by_uris(
            db_session,
            claimant_uri=doc_uri1.uri,
            uris=[doc_uri1.claimant, doc_uri2.claimant],
        )

        assert actual.count() == 1
        assert actual.first() == doc_uri1.document

    def test_with_no_existing_documents_we_create_one(self, db_session, factories):
        factories.DocumentURI()  # Noise
        db_session.flush()

        documents = Document.find_or_create_by_uris(
            db_session,
            claimant_uri="https://en.wikipedia.org/wiki/Pluto",
            uris=["https://m.en.wikipedia.org/wiki/Pluto"],
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
        "non_http_url",
        (
            "ftp://example.com",
            "android-app://example.com",
            "urn:x-pdf:example",
            "doi:http://example.com",
        ),
    )
    def test_it_ignores_all_non_http_urls(self, factories, non_http_url, url_type):
        self.assert_expected_web_uri_set(
            factories, [(non_http_url, url_type)], expected=None
        )

    def test_it_picks_the_first_http_value_when_the_types_are_the_same(
        self, factories, url_type
    ):
        self.assert_expected_web_uri_set(
            factories,
            [
                ("ftp://example.com/noise", url_type),
                ("http://example.com/first", url_type),
                ("https://example.com/second", url_type),
            ],
            expected="http://example.com/first",
        )

    @pytest.mark.parametrize(
        "higher,lower",
        (
            ("self-claim", "rel-canonical"),
            ("self-claim", "rel-shortlink"),
            ("rel-canonical", "rel-shortlink"),
        ),
    )
    def test_it_prefers_certain_types_over_others(self, factories, higher, lower):
        self.assert_expected_web_uri_set(
            factories,
            [
                ("https://example.com/lower", lower),
                ("https://example.com/higher", higher),
            ],
            expected="https://example.com/higher",
        )

    def assert_expected_web_uri_set(self, factories, document_uris, expected):
        document = factories.Document(
            document_uris=[
                factories.DocumentURI(uri=uri, type=uri_type)
                for uri, uri_type in document_uris
            ]
        )

        document.update_web_uri()

        assert document.web_uri == expected

    @pytest.fixture(params=("self-claim", "rel-canonical", "rel-shortlink"))
    def url_type(self, request):
        return request.param


@pytest.mark.usefixtures("duplicate_docs")
class TestMergeDocuments:
    def test_it_returns_the_first_doc(self, db_session, duplicate_docs):
        merged = merge_documents(db_session, duplicate_docs)

        assert merged == duplicate_docs[0]

    def test_it_deletes_all_but_the_first(self, db_session, duplicate_docs):
        merge_documents(db_session, duplicate_docs)
        db_session.flush()

        assert not (
            db_session.query(Document)
            .filter(Document.id.in_([duplicate_docs[1].id, duplicate_docs[2].id]))
            .count()
        )

    @pytest.mark.parametrize("updated", (None, _datetime(2001, 1, 1)))
    @pytest.mark.parametrize("sub_item", ("document_uris", "meta"))
    def test_it_moves_sub_items_to_the_first(
        self, db_session, duplicate_docs, datetime, updated, sub_item
    ):
        items = []
        for doc in duplicate_docs[1:]:
            items.extend(getattr(doc, sub_item))

        master = merge_documents(db_session, duplicate_docs, updated=updated)
        db_session.flush()

        assert [len(getattr(doc, sub_item)) for doc in duplicate_docs] == [3, 0, 0]

        expected_date = updated if updated else datetime.utcnow.return_value
        for item in items:
            assert item.document == master
            assert item.updated == expected_date

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
    @pytest.mark.parametrize(
        "created,updated", ((sentinel.created, sentinel.updated), (None, None))
    )
    def test_it_uses_the_target_uri_to_get_the_document(
        self, Document, caller, doc_uri_dicts, created, updated, datetime
    ):
        caller(
            session=sentinel.session,
            target_uri=sentinel.target_uri,
            document_uri_dicts=doc_uri_dicts,
            created=created,
            updated=updated,
        )

        expected_created = created if created else datetime.utcnow.return_value
        expected_updated = updated if updated else datetime.utcnow.return_value

        Document.find_or_create_by_uris.assert_called_once_with(
            sentinel.session,
            sentinel.target_uri,
            [data["uri"] for data in doc_uri_dicts],
            created=expected_created,
            updated=expected_updated,
        )

    def test_if_there_are_multiple_documents_it_merges_them_into_one(
        self, Document, merge_documents, caller
    ):
        Document.find_or_create_by_uris.return_value.count.return_value = 3

        result = caller(session=sentinel.session, updated=sentinel.updated)

        assert result == merge_documents.return_value
        merge_documents.assert_called_once_with(
            sentinel.session,
            Document.find_or_create_by_uris.return_value,
            updated=sentinel.updated,
        )

    def test_it_for_single_documents_we_return_the_first(self, Document, caller):
        Document.find_or_create_by_uris.return_value.count.return_value = 1

        result = caller()

        first = Document.find_or_create_by_uris.return_value.first
        first.assert_called_once_with()
        assert result == first.return_value

    def test_it_updates_document_updated(self, Document, caller):
        caller(updated=sentinel.updated)

        document = Document.find_or_create_by_uris.return_value.first.return_value
        assert document.updated == sentinel.updated

    def test_it_saves_all_the_document_uris(
        self, Document, create_or_update_document_uri, doc_uri_dicts, caller
    ):
        self.assert_sub_items_stored(
            Document,
            caller,
            field="document_uri_dicts",
            data_items=doc_uri_dicts,
            storage_fn=create_or_update_document_uri,
        )

    def test_it_updates_document_web_uri(self, Document, caller):
        Document.find_or_create_by_uris.return_value.count.return_value = 1

        caller()

        document = Document.find_or_create_by_uris.return_value.first.return_value
        document.update_web_uri.assert_called_once_with()

    def test_it_saves_all_the_document_metas(
        self, create_or_update_document_meta, Document, caller
    ):
        document_meta_dicts = [
            {
                "type": f"title_{i}",
                "value": f"value_{i}",
                "claimant": "http://example.com/claimant",
            }
            for i in range(3)
        ]

        self.assert_sub_items_stored(
            Document,
            caller,
            field="document_meta_dicts",
            data_items=document_meta_dicts,
            storage_fn=create_or_update_document_meta,
        )

    def assert_sub_items_stored(self, Document, caller, field, data_items, storage_fn):
        Document.find_or_create_by_uris.return_value.count.return_value = 1

        caller(
            session=sentinel.session,
            created=sentinel.created,
            updated=sentinel.updated,
            **{field: data_items},
        )

        assert storage_fn.call_count == len(data_items)

        for item in data_items:
            storage_fn.assert_any_call(
                session=sentinel.session,
                document=Document.find_or_create_by_uris.return_value.first.return_value,
                created=sentinel.created,
                updated=sentinel.updated,
                **item,
            )

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

    @pytest.fixture
    def caller(self):
        return functools.partial(
            update_document_metadata,
            session=sentinel.db_session,
            target_uri=sentinel.target_uri,
            created=sentinel.created,
            updated=sentinel.updated,
            document_meta_dicts=[],
            document_uri_dicts=[],
        )

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
def datetime(patch):
    datetime = patch("h.models.document._document.datetime")
    datetime.utcnow.return_value = _datetime.utcnow()

    return datetime
