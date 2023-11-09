from unittest.mock import sentinel

import pytest

from h.models import AnnotationMetadata
from h.services.annotation_metadata import AnnotationMetadataService, factory


class TestAnnotationMetadataService:
    def test_it(self, svc, factories, db_session):
        metadata = {"some": "data"}
        anno = factories.Annotation()
        anno_slim = factories.AnnotationSlim(annotation=anno)
        db_session.flush()

        svc.set(anno, metadata)

        anno_metadata = (
            db_session.query(AnnotationMetadata)
            .filter_by(annotation_id=anno_slim.id)
            .one()
        )
        assert anno_metadata.data == metadata

        # Second call updates the existing record
        metadata = {"new": "data"}
        svc.set(anno, metadata)
        db_session.refresh(anno_metadata)
        assert anno_metadata.data == metadata

    def test_factory(self, AnnotationMetadataService, db_session, pyramid_request):
        svc = factory(sentinel.context, pyramid_request)

        AnnotationMetadataService.assert_called_once_with(db=db_session)
        assert svc == AnnotationMetadataService.return_value

    @pytest.fixture
    def svc(self, db_session, pyramid_request):
        pyramid_request.db = db_session
        return AnnotationMetadataService(db_session)

    @pytest.fixture
    def AnnotationMetadataService(self, patch):
        return patch("h.services.annotation_metadata.AnnotationMetadataService")
