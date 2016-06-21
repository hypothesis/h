# -*- coding: utf-8 -*-
import pytest

from h import api
from h.groups import models

from ...common import factories


def test_init(db_session):
    name = "My Hypothesis Group"
    user = factories.User()

    group = models.Group(name=name, creator=user)
    db_session.add(group)
    db_session.flush()

    assert group.id
    assert group.name == name
    assert group.created
    assert group.updated
    assert group.creator == user
    assert group.creator_id == user.id
    assert group.members == [user]


def test_with_short_name():
    """Should raise ValueError if name shorter than 4 characters."""
    with pytest.raises(ValueError):
        models.Group(name="abc", creator=factories.User())


def test_with_long_name():
    """Should raise ValueError if name longer than 25 characters."""
    with pytest.raises(ValueError):
        models.Group(name="abcdefghijklmnopqrstuvwxyz",
                     creator=factories.User())


def test_slug(db_session):
    name = "My Hypothesis Group"
    user = factories.User()

    group = models.Group(name=name, creator=user)
    db_session.add(group)
    db_session.flush()

    assert group.slug == "my-hypothesis-group"


def test_repr(db_session):
    name = "My Hypothesis Group"
    user = factories.User()

    group = models.Group(name=name, creator=user)
    db_session.add(group)
    db_session.flush()

    assert repr(group) == "<Group: my-hypothesis-group>"


def test_created_by(db_session):
    name_1 = "My first group"
    name_2 = "My second group"
    user = factories.User()

    group_1 = models.Group(name=name_1, creator=user)
    group_2 = models.Group(name=name_2, creator=user)

    db_session.add(group_1, group_2)
    db_session.flush()

    assert models.Group.created_by(db_session, user).all() == [group_1, group_2]


@pytest.mark.usefixtures('documents')
def test_documents_returns_groups_annotated_documents(db_session, group):
    # Three different documents each with a shared annotation in the group.
    document_1 = document(db_session, 'http://example.com/document_1')
    annotation(db_session, document_1, groupid='test-group', shared=True)
    document_2 = document(db_session, 'http://example.com/document_2')
    annotation(db_session, document_2, groupid='test-group', shared=True)
    document_3 = document(db_session, 'http://example.com/document_3')
    annotation(db_session, document_3, groupid='test-group', shared=True)

    # In this test we don't care about other annotated documents that the
    # documents fixture might have created before we created our own.
    # We only care  that the first 3 documents returned are the 3 that we
    # created, in the right order.
    assert group.documents()[:3] == [document_3, document_2, document_1]


def test_documents_does_not_return_same_document_twice(documents, group):
    assert group.documents().count(
        documents['multiple_shared_annotations']) == 1


def test_documents_does_not_return_privately_annotated_documents(documents,
                                                                 group):
    returned_documents = group.documents()

    assert documents['only_private_annotations'] not in returned_documents


def test_documents_returns_documents_both_private_and_shared_annotations(
        documents, group):
    returned_documents = group.documents()

    assert documents['private_and_shared_annotations'] in returned_documents


def test_documents_does_not_return_other_groups_documents(documents, group):
    returned_documents = group.documents()

    assert documents['annotated_by_other_group'] not in returned_documents


def test_documents_returns_documents_annotated_by_this_group_and_another(
        documents, group):
    returned = group.documents()

    assert documents['annotated_by_this_group_and_another_group'] in returned


def test_documents_does_not_return_more_than_25_documents(db_session, group):
    for i in range(50):
        annotation(db_session,
                   document(db_session,
                            'http://example.com/document_' + str(i)),
                   groupid='test-group',
                   shared=True)

    assert len(group.documents()) == 25


def test_documents_passing_in_a_custom_limit(db_session, group):
    """It should obey a custom limit if one is passed in."""
    for i in range(50):
        annotation(db_session,
                   document(db_session,
                            'http://example.com/document_' + str(i)),
                   groupid='test-group',
                   shared=True)

    for limit in (10, 40):
        assert len(group.documents(limit=limit)) == limit


def test_documents_when_group_has_no_documents(group):
    assert group.documents() == []


def test_documents_does_not_return_null_documents(db_session, group):
    """
    It shouldn't return None when an annotation has no document.

    Some annotations have no document and annotation.document will be None.
    In this case nothing should be added to the list of documents,
    it should not return None in the list of documents that it returns.

    """
    db_session.add(api.models.Annotation(
        userid=u'fred', groupid=group.pubid, shared=True))

    assert None not in group.documents()


def annotation(session, document_, groupid, shared):
    """Add a new annotation of the given document to the db and return it."""
    annotation_ = api.models.Annotation(
        userid=u'fred', groupid=groupid, shared=shared,
        target_uri=document_.document_uris[0].uri)
    session.add(annotation_)
    return annotation_


def document(session, uri):
    """Add a new Document for the given uri to the db and return it."""
    document_ = api.models.Document()
    session.add(document_)

    # Flush the session so that document.id gets generated.
    session.flush()

    session.add(api.models.DocumentURI(
        claimant=uri, document_id=document_.id, uri=uri))

    return document_


@pytest.fixture
def documents(db_session):
    """Add diverse annotated documents to the db and return them."""
    # Document with one shared annotation.
    one_shared_annotation = document(db_session,
                                     'http://example.com/one_shared_annotation')
    annotation(db_session,
               one_shared_annotation,
               groupid='test-group',
               shared=True)

    # Document with multiple shared annotations.
    multiple_shared_annotations = document(db_session,
                                           'http://example.com/multiple_shared_annotations')
    for _ in range(3):
        annotation(db_session,
                   multiple_shared_annotations,
                   groupid='test-group',
                   shared=True)

    # Document with only private annotations.
    only_private_annotations = document(db_session,
                                        'http://example.com/only_private_annotations')
    annotation(db_session,
               only_private_annotations,
               groupid='test-group',
               shared=False)

    # Document with both private and shared annotations.
    private_and_shared_annotations = document(db_session,
                                              'http://example.com/private_and_shared_annotations')
    for shared in [True, False]:
        annotation(db_session,
                   private_and_shared_annotations,
                   groupid='test-group',
                   shared=shared)

    # Document annotated by other group.
    annotated_by_other_group = document(db_session,
                                        'http://example.com/annotated_by_other_group')
    annotation(db_session,
               annotated_by_other_group,
               groupid='other-group',
               shared=True)

    # Document annotated by both this group and another group.
    annotated_by_this_group_and_another_group = document(db_session,
                                                         'http://example.com/annotated_by_this_group_and_another_group')
    for groupid in ['test-group', 'other-group']:
        annotation(db_session,
                   annotated_by_this_group_and_another_group,
                   groupid=groupid,
                   shared=True)

    return dict(
        one_shared_annotation=one_shared_annotation,
        multiple_shared_annotations=multiple_shared_annotations,
        only_private_annotations=only_private_annotations,
        private_and_shared_annotations=private_and_shared_annotations,
        annotated_by_other_group=annotated_by_other_group,
        annotated_by_this_group_and_another_group=annotated_by_this_group_and_another_group,
    )


@pytest.fixture
def group(db_session):
    """Add a new group to the db and return it."""
    group_ = models.Group(name='test-group', creator=factories.User())
    db_session.add(group_)
    group_.pubid = 'test-group'
    return group_
