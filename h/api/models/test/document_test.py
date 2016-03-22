# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import datetime

import mock
import pytest

from h import db
from h.api.models import document
from h.api.models.document import Document, DocumentURI, DocumentMeta
from h.api.models.document import merge_documents


def test_document_title():
    doc = Document()
    DocumentMeta(type='title', value='The Title', document=doc, claimant='http://example.com')
    db.Session.add(doc)
    db.Session.flush()

    assert doc.title == 'The Title'


def test_document_title_returns_first():
    doc = Document()
    DocumentMeta(type='title', value='The US Title', document=doc, claimant='http://example.com')
    DocumentMeta(type='title', value='The UK Title', document=doc, claimant='http://example.co.uk')
    db.Session.add(doc)
    db.Session.flush()

    assert doc.title == 'The US Title'


def test_document_title_meta_not_found():
    doc = Document()
    DocumentMeta(type='other', value='something', document=doc, claimant='http://example.com')
    db.Session.add(doc)
    db.Session.flush()

    assert doc.title is None


def test_document_find_by_uris():
    document1 = Document()
    uri1 = 'https://de.wikipedia.org/wiki/Hauptseite'
    document1.document_uris.append(DocumentURI(claimant=uri1, uri=uri1))

    document2 = Document()
    uri2 = 'https://en.wikipedia.org/wiki/Main_Page'
    document2.document_uris.append(DocumentURI(claimant=uri2, uri=uri2))
    uri3 = 'https://en.wikipedia.org'
    document2.document_uris.append(DocumentURI(claimant=uri3, uri=uri2))

    db.Session.add_all([document1, document2])
    db.Session.flush()

    actual = Document.find_by_uris(db.Session, [
        'https://en.wikipedia.org/wiki/Main_Page',
        'https://m.en.wikipedia.org/wiki/Main_Page'])
    assert actual.count() == 1
    assert actual.first() == document2


def test_document_find_by_uris_no_matches():
    document = Document()
    document.document_uris.append(DocumentURI(
        claimant='https://en.wikipedia.org/wiki/Main_Page',
        uri='https://en.wikipedia.org/wiki/Main_Page'))
    db.Session.add(document)
    db.Session.flush()

    actual = Document.find_by_uris(db.Session, ['https://de.wikipedia.org/wiki/Hauptseite'])
    assert actual.count() == 0


def test_document_find_or_create_by_uris():
    document = Document()
    docuri1 = DocumentURI(
        claimant='https://en.wikipedia.org/wiki/Main_Page',
        uri='https://en.wikipedia.org/wiki/Main_Page',
        document=document)
    docuri2 = DocumentURI(
        claimant='https://en.wikipedia.org/wiki/http/en.m.wikipedia.org/wiki/Main_Page',
        uri='https://en.wikipedia.org/wiki/Main_Page',
        document=document)

    db.Session.add(docuri1)
    db.Session.add(docuri2)
    db.Session.flush()

    actual = Document.find_or_create_by_uris(db.Session,
        'https://en.wikipedia.org/wiki/Main_Page',
        ['https://en.wikipedia.org/wiki/http/en.m.wikipedia.org/wiki/Main_Page',
         'https://m.en.wikipedia.org/wiki/Main_Page'])
    assert actual.count() == 1
    assert actual.first() == document


def test_document_find_or_create_by_uris_no_results():
    document = Document()
    docuri = DocumentURI(
        claimant='https://en.wikipedia.org/wiki/Main_Page',
        uri='https://en.wikipedia.org/wiki/Main_Page',
        document=document)

    db.Session.add(docuri)
    db.Session.flush()

    documents = Document.find_or_create_by_uris(db.Session,
        'https://en.wikipedia.org/wiki/Pluto',
        ['https://m.en.wikipedia.org/wiki/Pluto'])

    assert documents.count() == 1

    actual = documents.first()
    assert isinstance(actual, Document)
    assert len(actual.document_uris) == 1

    docuri = actual.document_uris[0]
    assert docuri.claimant == 'https://en.wikipedia.org/wiki/Pluto'
    assert docuri.uri == 'https://en.wikipedia.org/wiki/Pluto'
    assert docuri.type == 'self-claim'


create_or_update_document_uri_fixtures = pytest.mark.usefixtures(
    'DocumentURI',
    'log',
)


def mock_docuri_dict(uri=None):
    """Return a mock docuri_dict for create_or_update_document_uri()."""
    if uri is None:
        uri = 'http://example.com/example_uri.html'

    now = datetime.datetime.now()

    return {
        'type': 'self-claim',
        'claimant': 'http://example.com/example_claimant.html',
        'uri': uri,
        'created': now,
        'updated': now
    }


def mock_document():
    """Return a mock Document object for create_or_update_document_uri()."""
    class Document:
        @property
        def id(self):
            pass
        @property
        def created(self):
            pass
        @property
        def updated(self):
            pass
    return mock.Mock(spec=Document)


def mock_db():
    """Return a mock db session object."""
    class DB:
        def add(self, obj):
            pass
    return mock.Mock(spec=DB())


@create_or_update_document_uri_fixtures
def test_create_or_update_document_uri_calls_filter(DocumentURI):
    document.create_or_update_document_uri(
        db=mock_db(),
        claimant='http://example.com/example_claimant.html',
        uri='http://example.com/example_uri.html',
        type='self-claim',
        content_type=None,
        document=mock_document(),
        created=datetime.datetime.now(),
        updated=datetime.datetime.now())

    # FIXME: We need to assert that this is called with the right arguments,
    # but that's very awkward to do with the way sqlalchemy querying works.'
    # Move this functionality onto the model class itself where the tests can
    # use the actual database.
    assert DocumentURI.query.filter.call_count == 1


@create_or_update_document_uri_fixtures
def test_create_or_update_document_uri_calls_first(DocumentURI):
    document.create_or_update_document_uri(
        db=mock_db(),
        claimant='http://example.com/example_claimant.html',
        uri='http://example.com/example_uri.html',
        type='self-claim',
        content_type=None,
        document=mock_document(),
        created=datetime.datetime.now(),
        updated=datetime.datetime.now())

    DocumentURI.query.filter.return_value.first.assert_called_once_with()


@create_or_update_document_uri_fixtures
def test_create_or_update_document_uri_inits_DocumentURI(DocumentURI):
    """If there's no matching object in the db it should init a new one."""
    DocumentURI.query.filter.return_value.first.return_value = None
    claimant = 'http://example.com/example_claimant.html'
    uri = 'http://example.com/example_uri.html'
    type_ = 'self-claim'
    content_type = 'text/html'
    document_ = mock_document()
    created = datetime.datetime.now() - datetime.timedelta(days=1)
    updated = datetime.datetime.now()

    document.create_or_update_document_uri(
        db=mock_db(),
        claimant=claimant,
        uri=uri,
        type=type_,
        content_type=content_type,
        document=document_,
        created=created,
        updated=updated)

    DocumentURI.assert_called_once_with(
        claimant=claimant,
        uri=uri,
        type=type_,
        content_type=content_type,
        document=document_,
        created=created,
        updated=updated)


@create_or_update_document_uri_fixtures
def test_create_or_update_document_uri_inits_DocumentURI_when_no_content_type(
        DocumentURI):
    """It shouldn't crash if docuri_dict contains no content_type."""
    DocumentURI.query.filter.return_value.first.return_value = None
    claimant = 'http://example.com/example_claimant.html'
    uri = 'http://example.com/example_uri.html'
    type_ = 'self-claim'
    content_type = None
    document_ = mock_document()
    created = datetime.datetime.now() - datetime.timedelta(days=1)
    updated = datetime.datetime.now()

    document.create_or_update_document_uri(
        db=mock_db(),
        claimant=claimant,
        uri=uri,
        type=type_,
        content_type=content_type,
        document=document_,
        created=created,
        updated=updated)

    DocumentURI.assert_called_once_with(
        claimant=claimant,
        uri=uri,
        type=type_,
        content_type=content_type,
        document=document_,
        created=created,
        updated=updated)


@create_or_update_document_uri_fixtures
def test_create_or_update_document_uri_adds_DocumentURI_to_db(DocumentURI):
    DocumentURI.query.filter.return_value.first.return_value = None
    db = mock_db()

    document.create_or_update_document_uri(
        db=db,
        claimant='http://example.com/example_claimant.html',
        uri='http://example.com/example_uri.html',
        type='self-claim',
        content_type=None,
        document=mock_document(),
        created=datetime.datetime.now(),
        updated=datetime.datetime.now())

    db.add.assert_called_once_with(DocumentURI.return_value)


@create_or_update_document_uri_fixtures
def test_create_or_update_document_uri_does_not_create_new_DocumentURI(DocumentURI):
    """It shouldn't create a new DocumentURI if one already exists."""
    DocumentURI.query.filter.return_value.first.return_value = mock.Mock()
    db = mock_db()

    document.create_or_update_document_uri(
        db=db,
        claimant='http://example.com/example_claimant.html',
        uri='http://example.com/example_uri.html',
        type='self-claim',
        content_type=None,
        document=mock_document(),
        created=datetime.datetime.now(),
        updated=datetime.datetime.now())

    assert not DocumentURI.called
    assert not db.add.called


@create_or_update_document_uri_fixtures
def test_create_or_update_document_uri_logs_warning_if_document_ids_differ(
        log,
        DocumentURI):
    """
    It should log a warning on Document objects mismatch.

    If there's an existing DocumentURI and its .document property is different
    to the given document it shoulg log a warning.

    """
    # existing_document_uri.document will not be equal to the given document'
    existing_document_uri = mock.Mock(document=mock_document())
    DocumentURI.query.filter.return_value.first.return_value = existing_document_uri

    document.create_or_update_document_uri(
        db=mock_db(),
        claimant='http://example.com/example_claimant.html',
        uri='http://example.com/example_uri.html',
        type='self-claim',
        content_type=None,
        document=mock_document(),
        created=datetime.datetime.now(),
        updated=datetime.datetime.now())

    assert log.warn.call_count == 1


@create_or_update_document_uri_fixtures
def test_create_or_update_document_uri_updates_updated_time(DocumentURI):
    # existing_document_uri has an older .updated time than than the updated
    # argument we will pass to create_or_update_document_uri().
    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(days=1)
    existing_document_uri = mock.Mock(updated=yesterday)

    DocumentURI.query.filter.return_value.first.return_value = (
        existing_document_uri)

    document.create_or_update_document_uri(
        db=mock_db(),
        claimant='http://example.com/example_claimant.html',
        uri='http://example.com/example_uri.html',
        type='self-claim',
        content_type=None,
        document=mock_document(),
        created=now - datetime.timedelta(days=3),
        updated=now)

    assert existing_document_uri.updated == now


@pytest.mark.usefixtures('DocumentMeta',
                         'log')
class TestCreateOrUpdateDocumentMeta(object):

    def test_it_calls_filter(self, DocumentMeta):
        document.create_or_update_document_meta(
            db=mock_db(),
            claimant='http://example.com/claimant',
            claimant_normalized='http://example.com/claimant_normalized',
            type='title',
            value='Example Page',
            document=mock.Mock(),
            created=yesterday(),
            updated=now(),
        )

        # FIXME: We need to assert that this is called with the right
        # arguments, but that's very awkward to do with the way sqlalchemy
        # querying works.' Move this functionality onto the model class itself
        # where the tests can use the actual database.
        assert DocumentMeta.query.filter.call_count == 1

    def test_it_calls_one_or_none(self, DocumentMeta):
        document.create_or_update_document_meta(
            db=mock_db(),
            claimant='http://example.com/claimant',
            claimant_normalized='http://example.com/claimant_normalized',
            type='title',
            value='Example Page',
            document=mock.Mock(),
            created=yesterday(),
            updated=now(),
        )

        DocumentMeta.query.filter.return_value.one_or_none\
            .assert_called_once_with()

    def test_it_creates_a_new_DocumentMeta(self, DocumentMeta):
        """It should create a new DocumentMeta if there isn't one already."""
        DocumentMeta.query.filter.return_value.one_or_none\
            .return_value = None
        claimant = 'http://example.com/claimant'
        claimant_normalized = 'http://example.com/claimant_normalized'
        type_ = 'title'
        value = 'Example Page'
        created = yesterday()
        updated = now()

        document.create_or_update_document_meta(
            db=mock_db(),
            claimant=claimant,
            claimant_normalized=claimant_normalized,
            type=type_,
            value=value,
            document=mock.sentinel.document,
            created=created,
            updated=updated,
        )

        DocumentMeta.assert_called_once_with(
            _claimant=claimant,
            _claimant_normalized=claimant_normalized,
            type=type_,
            value=value,
            document=mock.sentinel.document,
            created=created,
            updated=updated,
        )

    def test_it_adds_document_meta_to_db(self, DocumentMeta):
        """
        It should add the new DocumentMeta to the db.

        If there's no existing equivalent DocumentMeta already in the db then
        it should add the a new one to the db

        """
        db = mock_db()
        DocumentMeta.query.filter.return_value.one_or_none\
            .return_value = None

        document.create_or_update_document_meta(
            db=db,
            claimant='http://example.com/claimant',
            claimant_normalized='http://example.com/claimant_normalized',
            type='title',
            value='Example Page',
            document=mock.Mock(),
            created=yesterday(),
            updated=now(),
        )

        db.add.assert_called_once_with(DocumentMeta.return_value)

    def test_it_sets_value(self, DocumentMeta):
        """If there's an existing DocumentMeta it should update its value."""
        existing_document_meta = self.mock_document_meta()
        existing_document_meta.value = 'old value'
        DocumentMeta.query.filter.return_value.one_or_none\
            .return_value = existing_document_meta

        document.create_or_update_document_meta(
            db=mock_db(),
            claimant='http://example.com/claimant',
            claimant_normalized='http://example.com/claimant_normalized',
            type='title',
            value='new value',
            document=mock.Mock(),
            created=yesterday(),
            updated=now(),
        )

        assert existing_document_meta.value == 'new value'

    def test_sets_updated(self, DocumentMeta):
        """If there's an existing DocumentMeta it should update its updated."""
        existing_document_meta = self.mock_document_meta()
        existing_document_meta.updated = yesterday()
        DocumentMeta.query.filter.return_value.one_or_none\
            .return_value = existing_document_meta
        now_ = now()

        document.create_or_update_document_meta(
            db=mock_db(),
            claimant='http://example.com/claimant',
            claimant_normalized='http://example.com/claimant_normalized',
            type='title',
            value='new value',
            document=mock.Mock(),
            created=yesterday(),
            updated=now_,
        )

        assert existing_document_meta.updated == now_

    def test_it_logs_warning(self, DocumentMeta, log):
        """
        It should warn on document mismatches.

        It should warn if there's an existing DocumentMeta with a different
        Document.

        """
        document_one = mock_document()
        document_two = mock_document()
        existing_document_meta = self.mock_document_meta(document=document_one)
        DocumentMeta.query.filter.return_value.one_or_none\
            .return_value = existing_document_meta

        document.create_or_update_document_meta(
            db=mock_db(),
            claimant='http://example.com/claimant',
            claimant_normalized='http://example.com/claimant_normalized',
            type='title',
            value='new value',
            document=document_two,
            created=yesterday(),
            updated=now(),
        )

        assert log.warn.call_count == 1

    def mock_document_meta(self, document=None):
        class DocumentMeta(object):
            def __init__(self):
                self.claimant_normalized = None
                self.type = None
                self.value = None
                self.created = None
                self.updated = None
                self.document = document
                self.id = None
                self.document_id = None
        return mock.Mock(spec=DocumentMeta())


merge_documents_fixtures = pytest.mark.usefixtures('merge_data')


@merge_documents_fixtures
def test_merge_documents_returns_master(merge_data):
    master, duplicate = merge_data

    merged_master = merge_documents(db.Session, merge_data)
    assert merged_master == master


@merge_documents_fixtures
def test_merge_documents_deletes_duplicate_documents(merge_data):
    master, duplicate = merge_data

    merge_documents(db.Session, merge_data)
    db.Session.flush()

    assert Document.query.get(duplicate.id) is None


@merge_documents_fixtures
def test_merge_documents_rewires_document_uris(merge_data):
    master, duplicate = merge_data

    merge_documents(db.Session, merge_data)
    db.Session.flush()

    assert len(master.document_uris) == 2
    assert len(duplicate.document_uris) == 0


@merge_documents_fixtures
def test_merge_documents_rewires_document_meta(merge_data):
    master, duplicate = merge_data

    merge_documents(db.Session, merge_data)
    db.Session.flush()

    assert len(master.meta) == 2
    assert len(duplicate.meta) == 0


def now():
    return datetime.datetime.now()


def yesterday():
    return now() - datetime.timedelta(days=1)


@pytest.fixture
def DocumentURI(config, request):
    patcher = mock.patch('h.api.models.document.DocumentURI')
    DocumentURI = patcher.start()
    request.addfinalizer(patcher.stop)
    return DocumentURI


@pytest.fixture
def DocumentMeta(config, request):
    patcher = mock.patch('h.api.models.document.DocumentMeta')
    DocumentMeta = patcher.start()
    request.addfinalizer(patcher.stop)
    return DocumentMeta


@pytest.fixture
def merge_data(request):
    master = Document(document_uris=[DocumentURI(
            claimant='https://en.wikipedia.org/wiki/Main_Page',
            uri='https://en.wikipedia.org/wiki/Main_Page',
            type='self-claim')],
            meta=[DocumentMeta(
                claimant='https://en.wikipedia.org/wiki/Main_Page',
                type='title',
                value='Wikipedia, the free encyclopedia')])
    duplicate = Document(document_uris=[DocumentURI(
            claimant='https://m.en.wikipedia.org/wiki/Main_Page',
            uri='https://en.wikipedia.org/wiki/Main_Page',
            type='rel-canonical')],
            meta=[DocumentMeta(
                claimant='https://m.en.wikipedia.org/wiki/Main_Page',
                type='title',
                value='Wikipedia, the free encyclopedia')])

    db.Session.add_all([master, duplicate])
    db.Session.flush()
    return (master, duplicate)


@pytest.fixture
def log(config, request):
    patcher = mock.patch('h.api.models.document.log', autospec=True)
    log = patcher.start()
    request.addfinalizer(patcher.stop)
    return log
