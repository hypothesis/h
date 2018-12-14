# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import pytest

from h import events
from h.indexer import subscribers


@pytest.mark.usefixtures("add_annotation", "delete_annotation")
class TestSubscribeAnnotationEvent(object):
    @pytest.mark.parametrize("action", ["create", "update"])
    def test_it_enqueues_add_annotation_celery_task(
        self, action, add_annotation, delete_annotation, pyramid_request
    ):
        event = events.AnnotationEvent(
            pyramid_request, {"id": "test_annotation_id"}, action
        )

        subscribers.subscribe_annotation_event(event)

        add_annotation.delay.assert_called_once_with(event.annotation_id)
        assert not delete_annotation.delay.called

    def test_it_enqueues_delete_annotation_celery_task_for_delete(
        self, add_annotation, delete_annotation, pyramid_request
    ):
        event = events.AnnotationEvent(
            pyramid_request, {"id": "test_annotation_id"}, "delete"
        )

        subscribers.subscribe_annotation_event(event)

        delete_annotation.delay.assert_called_once_with(event.annotation_id)
        assert not add_annotation.delay.called

    @pytest.fixture
    def add_annotation(self, patch):
        return patch("h.indexer.subscribers.add_annotation")

    @pytest.fixture
    def delete_annotation(self, patch):
        return patch("h.indexer.subscribers.delete_annotation")
