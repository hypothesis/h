# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
from mock import Mock

from h.events import AnnotationEvent
from h.services.annotation_delete import annotation_delete_service_factory


class TestAnnotationDeleteService(object):
    def test_it_marks_the_annotation_as_deleted(
        self, svc, pyramid_request, factories, ann
    ):
        svc.delete(ann)

        assert ann.deleted

    def test_it_updates_the_updated_field(
        self, svc, pyramid_request, factories, ann, datetime
    ):
        svc.delete(ann)

        assert ann.updated == datetime.utcnow()

    def test_it_publishes_a_delete_event(self, svc, pyramid_request, factories, ann):
        svc.delete(ann)

        expected_event = AnnotationEvent(pyramid_request, ann.id, "delete")
        actual_event = pyramid_request.notify_after_commit.call_args[0][0]
        assert (
            expected_event.request,
            expected_event.annotation_id,
            expected_event.action,
        ) == (actual_event.request, actual_event.annotation_id, actual_event.action)


@pytest.fixture
def ann(factories):
    return factories.Annotation()


@pytest.fixture
def svc(db_session, pyramid_request):
    pyramid_request.db = db_session
    return annotation_delete_service_factory({}, pyramid_request)


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.notify_after_commit = Mock()
    return pyramid_request


@pytest.fixture
def datetime(patch):
    return patch("h.services.annotation_delete.datetime")
