# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from h.events import AnnotationEvent
from h.services.delete_group import delete_group_service_factory, DeleteGroupService


class TestDeleteGroupService(object):

    def test_delete_deletes_group(self, svc, db_session, factories):
        group = factories.Group()

        svc.delete(group)

        assert group in db_session.deleted

    def test_delete_deletes_annotations(self, svc, factories, storage, pyramid_request):
        group = factories.Group()
        annotations = [factories.Annotation(groupid=group.pubid),
                       factories.Annotation(groupid=group.pubid)]

        svc.delete(group)

        storage.delete_annotation.assert_has_calls([
            mock.call(pyramid_request.db, annotations[0].id),
            mock.call(pyramid_request.db, annotations[1].id),
        ], any_order=True)

    def test_delete_publishes_annotation_events(self, storage, factories, pyramid_request, svc):
        group = factories.Group()
        annotation = factories.Annotation(groupid=group.pubid)

        svc.delete(group)

        expected_event = AnnotationEvent(pyramid_request, annotation.id, 'delete')
        actual_event = pyramid_request.notify_after_commit.call_args[0][0]
        assert (expected_event.request, expected_event.annotation_id, expected_event.action) == \
               (actual_event.request, actual_event.annotation_id, actual_event.action)

    def test_delete_deletes_user_relationships(self, svc, db_session, factories):
        user = factories.User()
        group = factories.Group(creator=user)

        svc.delete(group)

        # note that user.groups retains deleted group through the request
        # until db is committed/flushed but the group is marked as deleted
        assert user.groups[0] in db_session.deleted
        assert user not in db_session.deleted

    def test_delete_group_factory(self, pyramid_request):
        svc = delete_group_service_factory(None, pyramid_request)

        assert isinstance(svc, DeleteGroupService)


@pytest.fixture
def svc(db_session, pyramid_request):
    pyramid_request.db = db_session
    return delete_group_service_factory({}, pyramid_request)


@pytest.fixture
def storage(patch):
    return patch('h.services.delete_group.storage')


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.notify_after_commit = mock.Mock()
    return pyramid_request
