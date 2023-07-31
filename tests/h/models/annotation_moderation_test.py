from h.models.annotation_moderation import AnnotationModeration


class TestAnnotationModeration:
    def test___repr__(self):
        moderation = AnnotationModeration(annotation_id=123)

        assert repr(moderation) == "<AnnotationModeration annotation_id=123>"
