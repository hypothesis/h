from h.models.legacy_annotation_moderation import _LegacyAnnotationModeration


class TestAnnotationModeration:
    def test___repr__(self):
        moderation = _LegacyAnnotationModeration(annotation_id=123)

        assert repr(moderation) == "<_LegacyAnnotationModeration annotation_id=123>"
