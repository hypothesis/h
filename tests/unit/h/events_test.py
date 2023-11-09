from unittest import mock

from h.events import AnnotationEvent

s = mock.sentinel


def test_annotation_event():
    evt = AnnotationEvent(s.request, s.annotation_id, s.action)

    assert evt.request == s.request
    assert evt.annotation_id == s.annotation_id
    assert evt.action == s.action
