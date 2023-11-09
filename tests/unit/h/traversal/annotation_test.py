from unittest.mock import sentinel

import pytest

from h.traversal import AnnotationContext, AnnotationRoot


@pytest.mark.usefixtures("annotation_read_service")
class TestAnnotationRoot:
    def test_getting_by_subscript_returns_AnnotationContext(
        self, root, AnnotationContext, annotation_read_service
    ):
        context = root[sentinel.annotation_id]

        annotation_read_service.get_annotation_by_id.assert_called_once_with(
            sentinel.annotation_id
        )
        AnnotationContext.assert_called_once_with(
            annotation_read_service.get_annotation_by_id.return_value
        )
        assert context == AnnotationContext.return_value

    def test_getting_by_subscript_raises_KeyError_if_annotation_missing(
        self, root, annotation_read_service
    ):
        annotation_read_service.get_annotation_by_id.return_value = None

        with pytest.raises(KeyError):
            assert root[sentinel.annotation_id]

    @pytest.fixture
    def root(self, pyramid_request):
        return AnnotationRoot(pyramid_request)

    @pytest.fixture
    def AnnotationContext(self, patch):
        return patch("h.traversal.annotation.AnnotationContext")


class TestAnnotationContext:
    def test_group(self, context):
        assert context.group == context.annotation.group

    @pytest.fixture
    def context(self, factories):
        return AnnotationContext(
            factories.Annotation.build(group=factories.Group.build())
        )
