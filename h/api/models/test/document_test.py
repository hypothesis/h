# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h import db
from h.api.models.document import Document, DocumentURI, DocumentMeta
from h.api.models.document import merge_documents


def test_document_find_by_uris():
    document1 = Document()
    uri1 = 'https://de.wikipedia.org/wiki/Hauptseite'
    document1.uris.append(DocumentURI(claimant=uri1, uri=uri1))

    document2 = Document()
    uri2 = 'https://en.wikipedia.org/wiki/Main_Page'
    document2.uris.append(DocumentURI(claimant=uri2, uri=uri2))
    uri3 = 'https://en.wikipedia.org'
    document2.uris.append(DocumentURI(claimant=uri3, uri=uri2))

    db.Session.add_all([document1, document2])
    db.Session.flush()

    actual = Document.find_by_uris(db.Session, [
        'https://en.wikipedia.org/wiki/Main_Page',
        'https://m.en.wikipedia.org/wiki/Main_Page'])
    assert actual.count() == 1
    assert actual.first() == document2


def test_document_find_by_uris_no_matches():
    document = Document()
    document.uris.append(DocumentURI(
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
    assert len(actual.uris) == 1

    docuri = actual.uris[0]
    assert docuri.claimant == 'https://en.wikipedia.org/wiki/Pluto'
    assert docuri.uri == 'https://en.wikipedia.org/wiki/Pluto'
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
            claimant='https://en.wikipedia.org/wiki/Main_Page',
            uri='https://en.wikipedia.org/wiki/Main_Page',
            type='self-claim')],
            meta=[DocumentMeta(
                claimant='https://en.wikipedia.org/wiki/Main_Page',
                type='title',
                value='Wikipedia, the free encyclopedia')])
    duplicate = Document(uris=[DocumentURI(
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
