from unittest.mock import sentinel

import pytest
from sqlalchemy import event

from h.models import Annotation
from h.services import AnnotationService
from h.services.annotation import service_factory


class TestAnnotationService:
    @pytest.mark.parametrize("reverse", (True, False))
    def test_get_annotations_by_id(self, svc, factories, reverse):
        annotations = factories.Annotation.create_batch(3)
        if reverse:
            annotations = list(reversed(annotations))

        results = svc.get_annotations_by_id(
            [annotation.id for annotation in annotations]
        )

        assert results == annotations

    def test_get_annotations_by_id_with_no_input(self, svc):
        assert not svc.get_annotations_by_id(ids=[])

    @pytest.mark.parametrize("attribute", ("document", "moderation", "group"))
    def test_get_annotations_by_id_preloading(
        self, svc, factories, db_session, query_counter, attribute
    ):
        annotation = factories.Annotation()

        # Ensure SQLAlchemy forgets all about our annotation
        db_session.flush()
        db_session.expire(annotation)
        svc.get_annotations_by_id(
            [annotation.id], eager_load=[getattr(Annotation, attribute)]
        )
        query_counter.reset()

        getattr(annotation, attribute)

        # If we preloaded, we shouldn't execute any queries
        assert not query_counter.count

    def test_search_annotations_with_document_uri(self, svc, factories):
        annotation = factories.Annotation()
        factories.Annotation()  # Add some noise

        results = svc.search_annotations(
            document_uri=annotation.document.document_uris[0].uri
        )

        assert results == [annotation]

    def test_search_annotations_with_target_uri_and_ids(self, svc, factories):
        annotation_1 = factories.Annotation()
        factories.Annotation(target_uri=annotation_1.target_uri)

        results = svc.search_annotations(
            ids=[annotation_1.id], target_uri=annotation_1.target_uri
        )

        assert results == [annotation_1]

    @pytest.fixture
    def query_counter(self, db_engine):
        class QueryCounter:
            count = 0

            def __call__(self, *args, **kwargs):
                self.count += 1

            def reset(self):
                self.count = 0

        query_counter = QueryCounter()
        event.listen(db_engine, "before_cursor_execute", query_counter)
        return query_counter

    @pytest.fixture
    def svc(self, db_session):
        return AnnotationService(db_session)


class TestServiceFactory:
    def test_it(self, pyramid_request, AnnotationService):
        svc = service_factory(sentinel.context, pyramid_request)

        AnnotationService.assert_called_once_with(db_session=pyramid_request.db)
        assert svc == AnnotationService.return_value

    @pytest.fixture
    def AnnotationService(self, patch):
        return patch("h.services.annotation.AnnotationService")
