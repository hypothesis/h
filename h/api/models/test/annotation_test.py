# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import security
import pytest

from h import db
from h.api.models.annotation import Annotation
from h.api.models.document import Document, DocumentURI


annotation_fixture = pytest.mark.usefixtures('annotation')


@annotation_fixture
def test_document(annotation):
    document = Document(document_uris=[DocumentURI(claimant=annotation.target_uri,
                                                   uri=annotation.target_uri)])
    db.Session.add(document)
    db.Session.flush()

    assert annotation.document == document


@annotation_fixture
def test_document_not_found(annotation):
    document = Document(document_uris=[DocumentURI(claimant='something-else',
                                                   uri='something-else')])
    db.Session.add(document)
    db.Session.flush()

    assert annotation.document is None


def test_parent_id_of_direct_reply():
    ann = Annotation(references=['parent_id'])

    assert ann.parent_id == 'parent_id'


def test_parent_id_of_reply_to_reply():
    ann = Annotation(references=['reply1', 'reply2', 'parent_id'])

    assert ann.parent_id == 'parent_id'


def test_parent_id_of_annotation():
    ann = Annotation()

    assert ann.parent_id is None


def test_acl_private():
    ann = Annotation(shared=False, userid='saoirse')
    actual = ann.__acl__()
    expect = [(security.Allow, 'saoirse', 'read'),
              (security.Allow, 'saoirse', 'admin'),
              (security.Allow, 'saoirse', 'update'),
              (security.Allow, 'saoirse', 'delete'),
              security.DENY_ALL]
    assert actual == expect


def test_acl_world_shared():
    ann = Annotation(shared=True, userid='saoirse', groupid='__world__')
    actual = ann.__acl__()
    expect = [(security.Allow, security.Everyone, 'read'),
              (security.Allow, 'saoirse', 'admin'),
              (security.Allow, 'saoirse', 'update'),
              (security.Allow, 'saoirse', 'delete'),
              security.DENY_ALL]
    assert actual == expect


def test_acl_group_shared():
    ann = Annotation(shared=True, userid='saoirse', groupid='lulapalooza')
    actual = ann.__acl__()
    expect = [(security.Allow, 'group:lulapalooza', 'read'),
              (security.Allow, 'saoirse', 'admin'),
              (security.Allow, 'saoirse', 'update'),
              (security.Allow, 'saoirse', 'delete'),
              security.DENY_ALL]
    assert actual == expect


@pytest.fixture
def annotation():
    ann = Annotation(userid="testuser", target_uri="http://example.com")

    db.Session.add(ann)
    db.Session.flush()
    return ann
