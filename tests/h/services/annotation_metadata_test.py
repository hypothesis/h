from unittest.mock import sentinel

import pytest

from h.models import AnnotationMetadata
from h.services.annotation_metadata import AnnotationMetadataService, factory


class TestAnnotationMetadataService:
    def test_it(self, svc, factories, decrypt_jwe_dict, db_session):
        decrypt_jwe_dict.side_effect = [{"some": "data"}, {"new": "data"}]
        anno = factories.Annotation()
        anno_slim = factories.AnnotationSlim(annotation=anno)
        db_session.flush()

        svc.set_annotation_metadata_from_jwe(anno, sentinel.jwe)

        decrypt_jwe_dict.assert_called_once_with("secret", sentinel.jwe)
        anno_metadata = (
            db_session.query(AnnotationMetadata)
            .filter_by(annotation_id=anno_slim.id)
            .one()
        )
        assert anno_metadata.data == {"some": "data"}

        # Second call updates the existing record
        svc.set_annotation_metadata_from_jwe(anno, sentinel.jwe)
        db_session.refresh(anno_metadata)
        assert anno_metadata.data == {"new": "data"}

    def test_factory(self, pyramid_request):
        svc = factory(sentinel.context, pyramid_request)

        assert isinstance(svc, AnnotationMetadataService)

    @pytest.fixture
    def decrypt_jwe_dict(self, patch):
        return patch("h.services.annotation_metadata.decrypt_jwe_dict")

    @pytest.fixture
    def svc(self, db_session, pyramid_request):
        pyramid_request.db = db_session
        return AnnotationMetadataService(db_session)

    @pytest.fixture(autouse=True)
    def environ(self, monkeypatch):
        monkeypatch.setenv("JWE_SECRET_LMS", "secret")
