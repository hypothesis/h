# -*- coding: utf-8 -*-

import mock

from h.api import events


class TestAnnotationEvent(object):
    def test_annotation_id(self):
        id_ = 'test-annotation-id'
        event = events.AnnotationEvent(mock.Mock(), {'id': id_}, 'create')
        assert event.annotation_id == id_

    def test_annotation_id_empty(self):
        event = events.AnnotationEvent(mock.Mock(), {}, 'create')
        assert event.annotation_id is None
