# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import datetime

import mock
import pytest

from h import db
from h.api.models import document


class TestDocumentTitle(object):

    def test_it_returns_the_value_of_the_one_title_DocumentMeta(self):
        """When there's only one DocumentMeta it should return its title."""
        doc = document.Document()
        document.DocumentMeta(type='title',
                              value='The Title',
                              document=doc,
                              claimant='http://example.com')
        db.Session.add(doc)
        db.Session.flush()

        assert doc.title == 'The Title'

    def test_it_returns_the_value_of_the_first_title_DocumentMeta(self):
        doc = document.Document()
        document.DocumentMeta(type='title',
                              value='The US Title',
                              document=doc,
                              claimant='http://example.com')
        document.DocumentMeta(type='title',
                              value='The UK Title',
                              document=doc,
                              claimant='http://example.co.uk')
        db.Session.add(doc)
        db.Session.flush()

        assert doc.title == 'The US Title'

    def test_it_returns_None_if_there_are_no_title_DocumentMetas(self):
        doc = document.Document()
        document.DocumentMeta(type='other',
                              value='something',
                              document=doc,
                              claimant='http://example.com')
        db.Session.add(doc)
        db.Session.flush()

        assert doc.title is None


class TestDocumentFindByURIs(object):

    def test_with_one_matching_Document(self):
        # One Document with a non-matching DocumentURI pointing to it.
        # find_by_uris() should not return this Document.
        document1 = document.Document()
        uri1 = 'https://de.wikipedia.org/wiki/Hauptseite'
        document1.document_uris.append(
            document.DocumentURI(claimant=uri1, uri=uri1))

        # A second Document with one matching and one non-matching DocumentURI
        # pointing to it. find_by_uris() should return this Document.
        document2 = document.Document()
        uri2 = 'https://en.wikipedia.org/wiki/Main_Page'
        document2.document_uris.append(
            document.DocumentURI(claimant=uri2, uri=uri2))
        uri3 = 'https://en.wikipedia.org'
        document2.document_uris.append(
            document.DocumentURI(claimant=uri3, uri=uri2))

        db.Session.add_all([document1, document2])
        db.Session.flush()

        actual = document.Document.find_by_uris(db.Session, [
            'https://en.wikipedia.org/wiki/Main_Page',
            'https://m.en.wikipedia.org/wiki/Main_Page'])

        assert actual.count() == 1
        assert actual.first() == document2

    def test_no_matches(self):
        document_ = document.Document()
        document_.document_uris.append(document.DocumentURI(
            claimant='https://en.wikipedia.org/wiki/Main_Page',
            uri='https://en.wikipedia.org/wiki/Main_Page'))
        db.Session.add(document_)
        db.Session.flush()

        actual = document.Document.find_by_uris(
            db.Session, ['https://de.wikipedia.org/wiki/Hauptseite'])
        assert actual.count() == 0


class TestDocumentFindOrCreateByURIs(object):

    def test_with_one_existing_Document(self):
        """
        When there's one matching Document it should return that Document.

        When searching with two URIs that match two DocumentURIs that both
        point to the same Document, it should return that Document.

        """
        document_ = document.Document()
        docuri1 = document.DocumentURI(
            claimant='https://en.wikipedia.org/wiki/Main_Page',
            uri='https://en.wikipedia.org/wiki/Main_Page',
            document=document_)
        docuri2 = document.DocumentURI(
            claimant='https://en.wikipedia.org/wiki/http/en.m.wikipedia.org/wiki/Main_Page',
            uri='https://en.wikipedia.org/wiki/Main_Page',
            document=document_)

        db.Session.add(docuri1)
        db.Session.add(docuri2)
        db.Session.flush()

        actual = document.Document.find_or_create_by_uris(db.Session,
            'https://en.wikipedia.org/wiki/Main_Page',
            ['https://en.wikipedia.org/wiki/http/en.m.wikipedia.org/wiki/Main_Page',
            'https://m.en.wikipedia.org/wiki/Main_Page'])

        assert actual.count() == 1
        assert actual.first() == document_

    def test_with_no_existing_documents(self):
        """When there are no matching Documents it creates and returns one."""
        document_ = document.Document()
        docuri = document.DocumentURI(
            claimant='https://en.wikipedia.org/wiki/Main_Page',
            uri='https://en.wikipedia.org/wiki/Main_Page',
            document=document_)

        db.Session.add(docuri)
        db.Session.flush()

        documents = document.Document.find_or_create_by_uris(
            db.Session,
            'https://en.wikipedia.org/wiki/Pluto',
            ['https://m.en.wikipedia.org/wiki/Pluto'])

        assert documents.count() == 1

        actual = documents.first()
        assert isinstance(actual, document.Document)
        assert len(actual.document_uris) == 1

        docuri = actual.document_uris[0]
        assert docuri.claimant == 'https://en.wikipedia.org/wiki/Pluto'
        assert docuri.uri == 'https://en.wikipedia.org/wiki/Pluto'
        assert docuri.type == 'self-claim'


@pytest.mark.usefixtures(
    'log',
)
class TestCreateOrUpdateDocumentURI(object):

    def test_it_updates_the_existing_DocumentURI_if_there_is_one(self):
        claimant = 'http://example.com/example_claimant.html'
        uri = 'http://example.com/example_uri.html'
        type_ = 'self-claim'
        content_type = None
        document_ = document.Document()
        created = yesterday()
        updated = yesterday()
        document_uri = document.DocumentURI(
            claimant=claimant,
            uri=uri,
            type=type_,
            content_type=content_type,
            document=document_,
            created=created,
            updated=updated,
        )
        db.Session.add(document_uri)

        mock_db = mock.Mock()
        now_ = now()
        document.create_or_update_document_uri(
            db=mock_db,
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
        assert not mock_db.add.called

    def test_it_creates_a_new_DocumentURI_if_there_is_no_existing_one(self):
        claimant = 'http://example.com/example_claimant.html'
        uri = 'http://example.com/example_uri.html'
        type_ = 'self-claim'
        content_type = None
        document_ = document.Document()
        created = yesterday()
        updated = yesterday()

        # Add one non-matching DocumentURI to the database.
        db.Session.add(document.DocumentURI(
            claimant=claimant,
            uri=uri,
            type=type_,
            # Different content_type means this DocumentURI should not match
            # the query.
            content_type='different',
            document=document_,
            created=created,
            updated=updated,
        ))

        document.create_or_update_document_uri(
            db=db.Session,
            claimant=claimant,
            uri=uri,
            type=type_,
            content_type=content_type,
            document=document_,
            created=now(),
            updated=now(),
        )

        document_uri = db.Session.query(document.DocumentURI).all()[-1]
        assert document_uri.claimant == claimant
        assert document_uri.uri == uri
        assert document_uri.type == type_
        assert document_uri.content_type == content_type
        assert document_uri.document == document_
        assert document_uri.created > created
        assert document_uri.updated > updated

    def test_it_logs_a_warning_if_document_ids_differ(self, log, DocumentURI):
        """
        It should log a warning on Document objects mismatch.

        If there's an existing DocumentURI and its .document property is
        different to the given document it shoulg log a warning.

        """
        # existing_document_uri.document won't be equal to the given document.
        existing_document_uri = mock.Mock(document=mock_document())
        DocumentURI.query.filter.return_value.first.return_value = (
            existing_document_uri)

        document.create_or_update_document_uri(
            db=mock_db(),
            claimant='http://example.com/example_claimant.html',
            uri='http://example.com/example_uri.html',
            type='self-claim',
            content_type=None,
            document=mock_document(),
            created=now(),
            updated=now())

        assert log.warn.call_count == 1

    @pytest.fixture
    def DocumentURI(self, request):
        patcher = mock.patch('h.api.models.document.DocumentURI')
        DocumentURI = patcher.start()
        request.addfinalizer(patcher.stop)
        return DocumentURI


class TestCreateOrUpdateDocumentMeta(object):

    def test_it_creates_a_new_DocumentMeta_if_there_is_no_existing_one(self):
        claimant = 'http://example.com/claimant'
        claimant_normalized = 'http://example.com/claimant_normalized'
        type_ = 'title'
        value = 'the title'
        document_ = document.Document()
        created = yesterday()
        updated = now()

        # Add one non-matching DocumentMeta to the database.
        # This should be ignored.
        db.Session.add(document.DocumentMeta(
            _claimant=claimant,
            _claimant_normalized=claimant_normalized,
            # Different type means this should not match the query.
            type='different',
            value=value,
            document=document_,
            created=created,
            updated=updated,
        ))

        document.create_or_update_document_meta(
            db=db.Session,
            claimant=claimant,
            claimant_normalized=claimant_normalized,
            type=type_,
            value=value,
            document=document_,
            created=created,
            updated=updated,
        )

        document_meta = db.Session.query(document.DocumentMeta).all()[-1]
        assert document_meta.claimant == claimant
        assert document_meta.claimant_normalized == claimant_normalized
        assert document_meta.type == type_
        assert document_meta.value == value
        assert document_meta.document == document_
        assert document_meta.created == created
        assert document_meta.updated == updated

    def test_it_updates_an_existing_DocumentMeta_if_there_is_one(self):
        claimant = 'http://example.com/claimant'
        claimant_normalized = 'http://example.com/claimant_normalized'
        type_ = 'title'
        value = 'the title'
        document_ = document.Document()
        created = yesterday()
        updated = now()
        document_meta = document.DocumentMeta(
            _claimant=claimant,
            _claimant_normalized=claimant_normalized,
            type=type_,
            value=value,
            document=document_,
            created=created,
            updated=updated,
        )
        db.Session.add(document_meta)

        mock_db = mock.Mock()
        new_updated = now()
        document.create_or_update_document_meta(
            db=mock_db,
            claimant=claimant,
            claimant_normalized=claimant_normalized,
            type=type_,
            value='new value',
            document=document.Document(),  # This should be ignored.
            created=now(),  # This should be ignored.
            updated=new_updated,
        )

        assert document_meta.value == 'new value'
        assert document_meta.updated == new_updated
        assert document_meta.created == created, "It shouldn't update created"
        assert document_meta.document == document_, (
            "It shouldn't update document")
        assert not mock_db.add.called

    def test_it_logs_a_warning(self, DocumentMeta, log):
        """
        It should warn on document mismatches.

        It should warn if there's an existing DocumentMeta with a different
        Document.

        """
        document_one = mock_document()
        document_two = mock_document()
        existing_document_meta = mock_document_meta(document=document_one)
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

    @pytest.fixture
    def DocumentMeta(self, request):
        patcher = mock.patch('h.api.models.document.DocumentMeta')
        DocumentMeta = patcher.start()
        request.addfinalizer(patcher.stop)
        return DocumentMeta


@pytest.mark.usefixtures('merge_data')
class TestMergeDocuments(object):

    def test_merge_documents_returns_master(self, merge_data):
        master, _ = merge_data

        merged_master = document.merge_documents(db.Session, merge_data)

        assert merged_master == master

    def test_merge_documents_deletes_duplicate_documents(self, merge_data):
        _, duplicate = merge_data

        document.merge_documents(db.Session, merge_data)
        db.Session.flush()

        assert document.Document.query.get(duplicate.id) is None

    def test_merge_documents_rewires_document_uris(self, merge_data):
        master, duplicate = merge_data

        document.merge_documents(db.Session, merge_data)
        db.Session.flush()

        assert len(master.document_uris) == 2
        assert len(duplicate.document_uris) == 0

    def test_merge_documents_rewires_document_meta(self, merge_data):
        master, duplicate = merge_data

        document.merge_documents(db.Session, merge_data)
        db.Session.flush()

        assert len(master.meta) == 2
        assert len(duplicate.meta) == 0

    @pytest.fixture
    def merge_data(self, request):
        master = document.Document(document_uris=[document.DocumentURI(
                claimant='https://en.wikipedia.org/wiki/Main_Page',
                uri='https://en.wikipedia.org/wiki/Main_Page',
                type='self-claim')],
                meta=[document.DocumentMeta(
                    claimant='https://en.wikipedia.org/wiki/Main_Page',
                    type='title',
                    value='Wikipedia, the free encyclopedia')])
        duplicate = document.Document(document_uris=[document.DocumentURI(
                claimant='https://m.en.wikipedia.org/wiki/Main_Page',
                uri='https://en.wikipedia.org/wiki/Main_Page',
                type='rel-canonical')],
                meta=[document.DocumentMeta(
                    claimant='https://m.en.wikipedia.org/wiki/Main_Page',
                    type='title',
                    value='Wikipedia, the free encyclopedia')])

        db.Session.add_all([master, duplicate])
        db.Session.flush()
        return (master, duplicate)


def now():
    return datetime.datetime.now()


def yesterday():
    return now() - datetime.timedelta(days=1)


def mock_db():
    """Return a mock db session object."""
    class DB(object):
        def add(self, obj):
            pass
    return mock.Mock(spec=DB())


def mock_document():
    """Return a mock Document object."""
    class Document(object):
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


def mock_document_meta(document=None):
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


@pytest.fixture
def log(config, request):
    patcher = mock.patch('h.api.models.document.log', autospec=True)
    log = patcher.start()
    request.addfinalizer(patcher.stop)
    return log
