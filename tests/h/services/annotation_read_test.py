from unittest.mock import sentinel

import pytest

from h.services.annotation_read import AnnotationReadService, service_factory


class TestAnnotationReadService:
    def test_get_annotation_by_id(self, svc, annotation):
        assert svc.get_annotation_by_id(annotation.id) == annotation

    def test_get_annotation_by_id_with_invalid_uuid(self, svc):
        assert not svc.get_annotation_by_id("NOTVALID")

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation()

    @pytest.fixture
    def svc(self, db_session):
        return AnnotationReadService(db_session=db_session)


class TestServiceFactory:
    def test_it(self, pyramid_request, AnnotationReadService):
        svc = service_factory(sentinel.context, pyramid_request)

        AnnotationReadService.assert_called_once_with(db_session=pyramid_request.db)
        assert svc == AnnotationReadService.return_value

    @pytest.fixture
    def AnnotationReadService(self, patch):
        return patch("h.services.annotation_read.AnnotationReadService")
