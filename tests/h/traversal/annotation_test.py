from unittest.mock import sentinel

import pytest

from h.traversal import AnnotationContext, AnnotationRoot


class TestAnnotationRoot:
    def test_create_permission_requires_authenticated_user(self, root, ACL):
        acl = root.__acl__()

        ACL.for_annotation.assert_called_once_with(annotation=None)
        assert acl == ACL.for_annotation.return_value

    def test_getting_by_subscript_returns_AnnotationContext(
        self,
        root,
        pyramid_request,
        AnnotationContext,
        storage,
        links_service,
    ):
        context = root[sentinel.annotation_id]

        storage.fetch_annotation.assert_called_once_with(
            pyramid_request.db, sentinel.annotation_id
        )
        AnnotationContext.assert_called_once_with(
            storage.fetch_annotation.return_value, links_service
        )
        assert context == AnnotationContext.return_value

    def test_getting_by_subscript_raises_KeyError_if_annotation_missing(
        self, root, storage
    ):
        storage.fetch_annotation.return_value = None

        with pytest.raises(KeyError):
            assert root[sentinel.annotation_id]

    @pytest.fixture
    def root(self, pyramid_request):
        return AnnotationRoot(pyramid_request)

    @pytest.fixture
    def storage(self, patch):
        return patch("h.traversal.annotation.storage")

    @pytest.fixture
    def AnnotationContext(self, patch):
        return patch("h.traversal.annotation.AnnotationContext")


class TestAnnotationContext:
    def test__acl__(self, context, ACL):
        context.allow_read_on_delete = sentinel.allow_read_on_delete

        acl = context.__acl__()

        ACL.for_annotation.assert_called_once_with(
            context.annotation,
            allow_read_on_delete=sentinel.allow_read_on_delete,
        )
        assert acl == ACL.for_annotation.return_value

    @pytest.fixture
    def context(self, annotation, links_service):
        return AnnotationContext(annotation, links_service)

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation()


@pytest.fixture(autouse=True)
def ACL(patch):
    return patch("h.traversal.annotation.ACL")
