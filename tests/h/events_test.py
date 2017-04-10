# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock

from h.events import AnnotationEvent, AnnotationTransformEvent

s = mock.sentinel


def test_annotation_event():
    evt = AnnotationEvent(s.request, s.annotation_id, s.action)

    assert evt.request == s.request
    assert evt.annotation_id == s.annotation_id
    assert evt.action == s.action


def test_annotation_transform_event():
    evt = AnnotationTransformEvent(s.request, s.annotation, s.annotation_dict)

    assert evt.request == s.request
    assert evt.annotation == s.annotation
    assert evt.annotation_dict == s.annotation_dict
