# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import mock

from h.events import AnnotationEvent
from h.services.annotation_delete import annotation_delete_service_factory


class TestAnnotationDeleteService(object):
    def test_it_marks_the_annotation_as_deleted(
        self, svc, pyramid_request, factories, annotation
    ):
        ann = annotation()
        svc.delete(ann)

        assert ann.deleted

    def test_it_updates_the_updated_field(
        self, svc, pyramid_request, factories, annotation, datetime
    ):
        ann = annotation()
        svc.delete(ann)

        assert ann.updated == datetime.utcnow.return_value

    def test_it_publishes_a_delete_event(
        self, svc, pyramid_request, factories, annotation
    ):
        ann = annotation()
        svc.delete(ann)

        expected_event = AnnotationEvent(pyramid_request, ann.id, "delete")
        actual_event = pyramid_request.notify_after_commit.call_args[0][0]
        assert (
            expected_event.request,
            expected_event.annotation_id,
            expected_event.action,
        ) == (actual_event.request, actual_event.annotation_id, actual_event.action)

    def test_it_deletes_all_annotations(
        self, svc, pyramid_request, factories, annotation
    ):
        svc.delete = mock.create_autospec(svc.delete, spec_set=True)

        anns = [annotation(), annotation()]
        svc.delete_annotations(anns)

        svc.delete.mock_calls == [mock.call(anns[0]), mock.call(anns[1])]


@pytest.fixture
def annotation(factories):
    return lambda factories=factories: factories.Annotation()


@pytest.fixture
def svc(db_session, pyramid_request):
    pyramid_request.db = db_session
    return annotation_delete_service_factory({}, pyramid_request)


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.notify_after_commit = mock.Mock()
    return pyramid_request


@pytest.fixture
def datetime(patch):
    return patch("h.services.annotation_delete.datetime")
