from datetime import datetime, timedelta
from unittest.mock import patch, sentinel

import pytest
from h_matchers import Any
from sqlalchemy import event

from h.models import Annotation
from h.schemas import ValidationError
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

    def test_update_annotation(
        self,
        svc,
        db_session,
        annotation,
        update_document_metadata,
        search_index,
        _validate_group,
    ):
        then = datetime.now() - timedelta(days=1)
        annotation.extra = {"key": "value"}
        annotation.updated = then

        result = svc.update_annotation(
            annotation,
            {
                "target_uri": "new_target_uri",
                "text": "new_text",
                "extra": {"extra_key": "extra_value"},
                "document": {
                    "document_meta_dicts": {"meta": 1},
                    "document_uri_dicts": {"uri": 1},
                },
            },
            update_timestamp=True,
        )

        _validate_group.assert_called_once_with(annotation)
        update_document_metadata.assert_called_once_with(
            db_session,
            result.target_uri,
            {"meta": 1},
            {"uri": 1},
            updated=result.updated,
        )

        # pylint: disable=protected-access
        search_index._queue.add_by_id.assert_called_once_with(
            annotation.id, tag="storage.update_annotation", schedule_in=60, force=False
        )
        assert result.document == update_document_metadata.return_value
        assert result.target_uri == "new_target_uri"
        assert result.text == "new_text"
        assert result.updated > then
        assert result.extra == {"key": "value", "extra_key": "extra_value"}

    def test_update_annotation_with_non_defaults(self, svc, annotation, search_index):
        then = datetime.now() - timedelta(days=1)
        annotation.updated = then

        result = svc.update_annotation(
            annotation, {}, update_timestamp=False, reindex_tag="custom_tag"
        )

        # pylint: disable=protected-access
        search_index._queue.add_by_id.assert_called_once_with(
            Any(), tag="custom_tag", schedule_in=Any(), force=True
        )
        assert result.updated == then

    def test__validate_group_with_no_group(self, svc, annotation):
        annotation.group = None

        with pytest.raises(ValidationError):
            svc._validate_group(annotation)  # pylint: disable=protected-access

    @pytest.mark.parametrize("enforce_scope", (True, False))
    @pytest.mark.parametrize("matching_scope", (True, False))
    @pytest.mark.parametrize("has_scopes", (True, False))
    def test__validate_group_with_url_not_in_scopes(
        self, svc, annotation, factories, enforce_scope, matching_scope, has_scopes
    ):
        annotation.group.enforce_scope = enforce_scope
        annotation.target_uri = "http://scope" if matching_scope else "http://MISMATCH"
        if has_scopes:
            annotation.group.scopes = [factories.GroupScope(scope="http://scope")]

        if enforce_scope and has_scopes and not matching_scope:
            with pytest.raises(ValidationError):
                svc._validate_group(annotation)  # pylint: disable=protected-access
        else:
            svc._validate_group(annotation)  # pylint: disable=protected-access

    @pytest.fixture
    def _validate_group(self, svc):
        with patch.object(svc, "_validate_group") as _validate_group:
            yield _validate_group

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
    def annotation(self, factories):
        return factories.Annotation()

    @pytest.fixture
    def svc(self, db_session, search_index):
        return AnnotationService(
            db_session=db_session, search_index_service=search_index
        )

    @pytest.fixture(autouse=True)
    def update_document_metadata(self, patch, factories):
        update_document_metadata = patch(
            "h.services.annotation.update_document_metadata"
        )
        update_document_metadata.return_value = factories.Document()
        return update_document_metadata


class TestServiceFactory:
    def test_it(self, pyramid_request, AnnotationService, search_index):
        svc = service_factory(sentinel.context, pyramid_request)

        AnnotationService.assert_called_once_with(
            db_session=pyramid_request.db, search_index_service=search_index
        )
        assert svc == AnnotationService.return_value

    @pytest.fixture
    def AnnotationService(self, patch):
        return patch("h.services.annotation.AnnotationService")
