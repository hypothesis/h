# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import security
import pytest

from h.api.models.annotation import Annotation
from h.api.models.document import Document, DocumentURI


annotation_fixture = pytest.mark.usefixtures('annotation')


@annotation_fixture
def test_document(annotation, db_session):
    document = Document(document_uris=[DocumentURI(claimant=annotation.target_uri,
                                                   uri=annotation.target_uri)])
    db_session.add(document)
    db_session.flush()

    assert annotation.document == document


@annotation_fixture
def test_document_not_found(annotation, db_session):
    document = Document(document_uris=[DocumentURI(claimant='something-else',
                                                   uri='something-else')])
    db_session.add(document)
    db_session.flush()

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


def test_thread_root_id_returns_id_if_no_references():
    annotation = Annotation(id='GBhy1DoHEea6htPothzqZQ')

    assert annotation.thread_root_id == 'GBhy1DoHEea6htPothzqZQ'


def test_thread_root_id_returns_id_if_references_empty():
    annotation = Annotation(id='jANlljoHEea6hsv8FY7ipw',
                            references=[])

    assert annotation.thread_root_id == 'jANlljoHEea6hsv8FY7ipw'


def test_thread_root_id_returns_reference_if_only_one_reference():
    annotation = Annotation(id='qvJnIjoHEea6hiv0nJK7gw',
                            references=['yiSVIDoHEea6hjcSFuROLw'])

    assert annotation.thread_root_id == 'yiSVIDoHEea6hjcSFuROLw'


def test_thread_root_id_returns_first_reference_if_many_references():
    annotation = Annotation(id='uK9yVjoHEea6hsewWuiKtQ',
                            references=['1Ife3DoHEea6hpv8vWujdQ',
                                        'uVuItjoHEea6hiNgv1wvmg',
                                        'Qe7fpc5ZRgWy0RSHEP9UNg'])

    assert annotation.thread_root_id == '1Ife3DoHEea6hpv8vWujdQ'


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


def test_setting_extras_inline_is_persisted(db_session):
    """
    In-place changes to Annotation.extra should be persisted.

    Setting an Annotation.extra value in-place:

        my_annotation.extra['foo'] = 'bar'

    should be persisted to the database.

    """
    annotation = Annotation(userid='fred')
    db_session.add(annotation)

    # We need to flush the db here so that the default value for
    # annotation.extra gets persisted and out mutation of annotation.extra
    # below happens when the previous value is already persisted, otherwise
    # this test would never fail.
    db_session.flush()

    annotation.extra['foo'] = 'bar'

    # We need to commit the db session here so that the in-place change to
    # annotation.extra above would be lost if annotation.extra was a normal
    # dict. Without this commit() this test would never fail.
    db_session.commit()

    annotation = db_session.query(Annotation).get(annotation.id)

    assert annotation.extra == {'foo': 'bar'}


def test_deleting_extras_inline_is_persisted(db_session):
    """
    In-place changes to Annotation.extra should be persisted.

    Deleting an Annotation.extra value in-place should be persisted to the
    database.

    """
    annotation = Annotation(userid='fred')
    annotation.extra = {'foo': 'bar'}
    db_session.add(annotation)
    db_session.flush()

    del annotation.extra['foo']
    db_session.commit()
    annotation = db_session.query(Annotation).get(annotation.id)

    assert 'foo' not in annotation.extra


def test_appending_tags_inline_is_persisted(db_session):
    """
    In-place changes to Annotation.tags should be persisted.

    Changes made by Annotation.tags.append() should be persisted to the
    database.

    """
    annotation = Annotation(userid='fred')
    annotation.tags = []  # FIXME: Annotation should have a default value here.
    db_session.add(annotation)
    db_session.flush()

    annotation.tags.append('foo')
    db_session.commit()
    annotation = db_session.query(Annotation).get(annotation.id)

    assert 'foo' in annotation.tags


def test_deleting_tags_inline_is_persisted(db_session):
    """In-place deletions of annotation tags should be persisted."""
    annotation = Annotation(userid='fred')
    annotation.tags = ['foo']
    db_session.add(annotation)
    db_session.flush()

    del annotation.tags[0]
    db_session.commit()
    annotation = db_session.query(Annotation).get(annotation.id)

    assert 'foo' not in annotation.tags


@pytest.fixture
def annotation(db_session):
    ann = Annotation(userid="testuser", target_uri="http://example.com")

    db_session.add(ann)
    db_session.flush()
    return ann
