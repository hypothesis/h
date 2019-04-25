# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.services.document import DocumentService


class TestFetchByGroupid(object):
    def test_it_returns_documents_annotated_within_group(
        self, svc, groups, annotations, matchers
    ):
        docs = svc.fetch_by_groupid(groupid=groups["target_group"].pubid)

        assert docs == matchers.UnorderedList([anno.document for anno in annotations])

    def test_it_does_not_return_documents_annotated_in_other_groups(
        self, groups, annotations, other_annotations, svc, matchers
    ):
        docs = svc.fetch_by_groupid(groupid=groups["target_group"].pubid)
        for other_anno in other_annotations:
            assert other_anno.document not in docs

    def test_it_returns_each_document_only_once(
        self, svc, groups, annotations, db_session
    ):
        # This will make both annotations point to the same document
        annotations[1].document = annotations[0].document
        annotations[2].document = annotations[0].document
        docs = svc.fetch_by_groupid(groupid=groups["target_group"].pubid)

        # But only one instance of the document is returned
        assert docs == [annotations[0].document]

    def test_it_returns_only_documents_with_shared_annotations_when_no_user(
        self, annotations, groups, svc, db_session
    ):
        annotations[1].shared = False
        annotations[2].shared = False

        docs = svc.fetch_by_groupid(groupid=groups["target_group"].pubid)

        assert docs == [annotations[0].document]

    def test_it_returns_only_documents_with_visible_annotations_for_user(
        self, svc, annotations, groups, target_user, other_user, db_session, matchers
    ):
        # This makes an "only me" annotation, associated with our target user
        annotations[1].shared = False
        annotations[1].userid = target_user.userid

        # This makes an "only me" annotation, associated with a different user
        annotations[2].shared = False
        annotations[2].userid = other_user.userid

        docs = svc.fetch_by_groupid(
            groupid=groups["target_group"].pubid, userid=target_user.userid
        )

        # The "only me" annotation for THIS user should be returned, but not the
        # "only me" annotation associated with another user
        assert docs == matchers.UnorderedList(
            [annotations[0].document, annotations[1].document]
        )

    def test_it_returns_documents_ordered_by_last_activity_desc(
        self, svc, annotations, groups, factories, db_session, matchers
    ):
        # Update the document associated with ``annotations[1]``...
        annotations[1].document.title = "Bleep bloop"

        # this will create the newest/latest document in the DB
        new_annotation = factories.Annotation(
            groupid=groups["target_group"].pubid, shared=True
        )

        docs = svc.fetch_by_groupid(groupid=groups["target_group"].pubid)

        # ``new_annotation`` has the most recently-updated document, followed by
        # the updated ``annotations[1]``, then the other two annotation's
        # documents in reverse created (i.e. updated) order
        assert docs == [
            new_annotation.document,
            annotations[1].document,
            annotations[2].document,
            annotations[0].document,
        ]


@pytest.fixture
def target_user(factories):
    return factories.User()


@pytest.fixture
def other_user(factories):
    return factories.User()


@pytest.fixture
def groups(factories):
    return {"target_group": factories.Group(), "other_group": factories.Group()}


@pytest.fixture
def annotations(factories, groups):
    return [
        factories.Annotation(groupid=groups["target_group"].pubid, shared=True),
        factories.Annotation(groupid=groups["target_group"].pubid, shared=True),
        factories.Annotation(groupid=groups["target_group"].pubid, shared=True),
    ]


@pytest.fixture
def other_annotations(factories, groups):
    return [
        factories.Annotation(groupid=groups["other_group"].pubid, shared=True),
        factories.Annotation(groupid=groups["other_group"].pubid, shared=True),
        factories.Annotation(groupid=groups["other_group"].pubid, shared=True),
    ]


@pytest.fixture
def svc(db_session):
    return DocumentService(session=db_session)
