# pylint:disable=protected-access
from unittest import mock

import pytest

from h import models
from h.cli.commands import normalize_uris


def test_it_normalizes_document_uris_uri(req):
    docuri_1 = models.DocumentURI(
        _claimant="http://example.org/",
        _claimant_normalized="http://example.org",
        _uri="http://example.org/",
        _uri_normalized="http://example.org",
        type="self-claim",
    )
    docuri_2 = models.DocumentURI(
        _claimant="http://example.org/",
        _claimant_normalized="http://example.org",
        _uri="https://example.org/",
        _uri_normalized="https://example.org",
        type="rel-canonical",
    )

    req.db.add(models.Document(document_uris=[docuri_1, docuri_2]))
    req.db.flush()

    normalize_uris.normalize_document_uris(req)

    assert docuri_1.uri_normalized == "httpx://example.org"
    assert docuri_2.uri_normalized == "httpx://example.org"


def test_it_normalizes_document_uris_claimant(req):
    docuri_1 = models.DocumentURI(
        _claimant="http://example.org/",
        _claimant_normalized="http://example.org",
        _uri="http://example.org/",
        _uri_normalized="http://example.org",
        type="self-claim",
    )
    docuri_2 = models.DocumentURI(
        _claimant="http://example.org/",
        _claimant_normalized="http://example.org",
        _uri="https://example.org/",
        _uri_normalized="https://example.org",
        type="rel-canonical",
    )

    req.db.add(models.Document(document_uris=[docuri_1, docuri_2]))
    req.db.flush()

    normalize_uris.normalize_document_uris(req)

    assert docuri_1.claimant_normalized == "httpx://example.org"
    assert docuri_2.claimant_normalized == "httpx://example.org"


def test_it_deletes_duplicate_document_uri_objects(req):
    docuri_1 = models.DocumentURI(
        _claimant="http://example.org/",
        _claimant_normalized="http://example.org",
        _uri="http://example.org/",
        _uri_normalized="http://example.org",
        type="self-claim",
    )
    docuri_2 = models.DocumentURI(
        _claimant="https://example.org/",
        _claimant_normalized="https://example.org",
        _uri="https://example.org/",
        _uri_normalized="https://example.org",
        type="self-claim",
    )

    req.db.add(models.Document(document_uris=[docuri_1, docuri_2]))
    req.db.flush()

    normalize_uris.normalize_document_uris(req)

    assert req.db.query(models.DocumentURI).count() == 1


def test_it_merges_documents_when_duplicates_found(req):
    docuri_1 = models.DocumentURI(
        claimant="http://example.org/", uri="http://example.org/", type="self-claim"
    )
    docuri_2 = models.DocumentURI(
        claimant="https://example.net/",
        uri="https://example.org/",
        type="rel-canonical",
    )

    req.db.add_all(
        [
            models.Document(document_uris=[docuri_1]),
            models.Document(document_uris=[docuri_2]),
        ]
    )
    req.db.flush()

    normalize_uris.normalize_document_uris(req)

    assert req.db.query(models.Document).count() == 1


def test_it_normalizes_document_meta_claimant(req):
    docmeta_1 = models.DocumentMeta(
        _claimant="http://example.org/",
        _claimant_normalized="http://example.org",
        type="title",
        value=["Test Title"],
    )
    docmeta_2 = models.DocumentMeta(
        _claimant="http://example.net/",
        _claimant_normalized="http://example.net",
        type="title",
        value=["Test Title"],
    )

    req.db.add(models.Document(meta=[docmeta_1, docmeta_2]))
    req.db.flush()

    normalize_uris.normalize_document_meta(req)

    assert docmeta_1.claimant_normalized == "httpx://example.org"
    assert docmeta_2.claimant_normalized == "httpx://example.net"


def test_it_deletes_duplicate_document_meta_objects(req):
    docmeta_1 = models.DocumentMeta(
        _claimant="http://example.org/", type="title", value=["Test Title"]
    )
    docmeta_1._claimant_normalized = "http://example.org"
    docmeta_2 = models.DocumentMeta(
        _claimant="https://example.org/", type="title", value=["Test Title"]
    )
    docmeta_2._claimant_normalized = "https://example.org"

    req.db.add_all(
        [models.Document(meta=[docmeta_1]), models.Document(meta=[docmeta_2])]
    )
    req.db.flush()

    normalize_uris.normalize_document_meta(req)

    assert req.db.query(models.DocumentMeta).count() == 1


@pytest.mark.usefixtures("index")
def test_it_normalizes_annotation_target_uri(req, factories, db_session):
    annotation_1 = factories.Annotation(userid="luke", target_uri="http://example.org/")
    annotation_1._target_uri_normalized = "http://example.org"
    annotation_2 = factories.Annotation(userid="luke", target_uri="http://example.net/")
    annotation_2._target_uri_normalized = "http://example.net"
    db_session.flush()

    normalize_uris.normalize_annotations(req)

    assert annotation_1.target_uri_normalized == "httpx://example.org"
    assert annotation_2.target_uri_normalized == "httpx://example.net"


def test_it_reindexes_changed_annotations(req, index, factories, db_session):
    annotation_1 = factories.Annotation(userid="luke", target_uri="http://example.org/")
    annotation_1._target_uri_normalized = "http://example.org"
    annotation_2 = factories.Annotation(userid="luke", target_uri="http://example.net/")
    annotation_2._target_uri_normalized = "http://example.net"
    db_session.flush()

    indexer = index.BatchIndexer.return_value
    indexer.index.return_value = None

    normalize_uris.normalize_annotations(req)

    indexer.index.assert_called_once_with({annotation_1.id, annotation_2.id})


def test_it_skips_reindexing_unaltered_annotations(req, index, factories, db_session):
    factories.Annotation(userid="luke", target_uri="http://example.org/")
    annotation_2 = factories.Annotation(userid="luke", target_uri="http://example.net/")
    annotation_2._target_uri_normalized = "http://example.net"
    db_session.flush()

    indexer = index.BatchIndexer.return_value
    indexer.index.return_value = None

    normalize_uris.normalize_annotations(req)

    indexer.index.assert_called_once_with({annotation_2.id})


@pytest.fixture
def req(pyramid_request):
    pyramid_request.tm = mock.MagicMock()
    pyramid_request.es = mock.MagicMock()
    return pyramid_request


@pytest.fixture
def index(patch):
    return patch("h.cli.commands.normalize_uris.index")
