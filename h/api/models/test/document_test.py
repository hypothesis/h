# -*- coding: utf-8 -*-

import pytest

from h import db
from h.api.models.document import Document, DocumentURI, DocumentMeta
from h.api.models.document import merge_documents


def test_document_find_or_create_by_uris():
    document = Document()
    docuri1 = DocumentURI(
        claimant=u'https://en.wikipedia.org/wiki/Main_Page',
        uri=u'https://en.wikipedia.org/wiki/Main_Page',
        document=document)
    docuri2 = DocumentURI(
        claimant=u'https://en.wikipedia.org/wiki/http/en.m.wikipedia.org/wiki/Main_Page',
        uri=u'https://en.wikipedia.org/wiki/Main_Page',
        document=document)

    db.Session.add(docuri1)
    db.Session.add(docuri2)
    db.Session.flush()

    actual = Document.find_or_create_by_uris(
        u'https://en.wikipedia.org/wiki/Main_Page',
        [u'https://en.wikipedia.org/wiki/http/en.m.wikipedia.org/wiki/Main_Page',
         u'https://m.en.wikipedia.org/wiki/Main_Page'])
    assert actual.count() == 1
    assert actual.first() == document


def test_document_find_by_uris_no_results():
    document = Document()
    docuri = DocumentURI(
        claimant=u'https://en.wikipedia.org/wiki/Main_Page',
        uri=u'https://en.wikipedia.org/wiki/Main_Page',
        document=document)

    db.Session.add(docuri)
    db.Session.flush()

    documents = Document.find_or_create_by_uris(
        u'https://en.wikipedia.org/wiki/Pluto',
        [u'https://m.en.wikipedia.org/wiki/Pluto'])

    assert documents.count() == 1

    actual = documents.first()
    assert isinstance(actual, Document)
    assert len(actual.uris) == 1

    docuri = actual.uris[0]
    assert docuri.claimant == u'https://en.wikipedia.org/wiki/Pluto'
    assert docuri.uri == u'https://en.wikipedia.org/wiki/Pluto'
    assert docuri.type == 'self-claim'


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

    assert len(master.uris) == 2
    assert len(duplicate.uris) == 0

@merge_documents_fixtures
def test_merge_documents_rewires_document_meta(merge_data):
    master, duplicate = merge_data

    merge_documents(db.Session, merge_data)
    db.Session.flush()

    assert len(master.meta) == 2
    assert len(duplicate.meta) == 0


@pytest.fixture
def merge_data(request):
    master = Document(uris=[DocumentURI(
            claimant=u'https://en.wikipedia.org/wiki/Main_Page',
            uri=u'https://en.wikipedia.org/wiki/Main_Page',
            type=u'self-claim')],
            meta=[DocumentMeta(
                claimant=u'https://en.wikipedia.org/wiki/Main_Page',
                type=u'title',
                value=u'Wikipedia, the free encyclopedia')])
    duplicate = Document(uris=[DocumentURI(
            claimant=u'https://m.en.wikipedia.org/wiki/Main_Page',
            uri=u'https://en.wikipedia.org/wiki/Main_Page',
            type=u'rel-canonical')],
            meta=[DocumentMeta(
                claimant=u'https://m.en.wikipedia.org/wiki/Main_Page',
                type=u'title',
                value=u'Wikipedia, the free encyclopedia')])

    db.Session.add_all([master, duplicate])
    db.Session.flush()
    return (master, duplicate)
