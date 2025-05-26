from unittest import mock

from h.events import AnnotationEvent, ModeratedAnnotationEvent

s = mock.sentinel


def test_annotation_event():
    evt = AnnotationEvent(s.request, s.annotation_id, s.action)

    assert evt.request == s.request
    assert evt.annotation_id == s.annotation_id
    assert evt.action == s.action


def test_moderation_annotation_event():
    evt = ModeratedAnnotationEvent(s.request, s.moderation_log_id)

    assert evt.request == s.request
    assert evt.moderation_log_id == s.moderation_log_id
