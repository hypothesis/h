from unittest.mock import Mock, call, patch, sentinel

import pytest

from h.services.url_migration import URLMigrationService


class TestURLMigrationService:
    def test_move_annotations(
        self, svc, annotation_service, factories, transform_document
    ):
        annotation = factories.Annotation(
            target_selectors=[
                {"type": "a", "other": "existing"},
                {"type": "b", "other": "existing"},
            ]
        )
        annotation_service.search_annotations.return_value = [annotation]

        svc.move_annotations(
            annotation_ids=sentinel.annotation_ids,
            current_uri=sentinel.current_uri,
            new_url_info={
                "url": sentinel.new_url,
                "document": sentinel.document,
                "selectors": [
                    {"type": "b", "other": "new"},
                    {"type": "c", "other": "new"},
                ],
            },
        )

        annotation_service.search_annotations.assert_called_once_with(
            ids=sentinel.annotation_ids, target_uri=sentinel.current_uri
        )
        transform_document.assert_called_once_with(sentinel.document, sentinel.new_url)
        annotation_service.update_annotation.assert_called_once_with(
            annotation,
            {
                "target_uri": sentinel.new_url,
                "document": transform_document.return_value,
                "target_selectors": [
                    {"type": "a", "other": "existing"},
                    {"type": "b", "other": "existing"},
                    {"type": "c", "other": "new"},
                ],
            },
            update_timestamp=False,
            reindex_tag="URLMigrationService.move_annotations",
        )

    def test_move_annotations_minimal_example(
        self, svc, annotation_service, factories, transform_document
    ):
        annotation = factories.Annotation()
        annotation_service.search_annotations.return_value = [annotation]

        svc.move_annotations(
            annotation_ids=sentinel.annotation_ids,
            current_uri=sentinel.current_uri,
            new_url_info={
                "url": sentinel.new_url,
            },
        )

        transform_document.assert_not_called()

    def test_move_annotations_by_url(
        self,
        svc,
        factories,
        transaction_manager,
        annotation_service,
        move_annotations,
        move_annotations_task,
    ):
        annotations = factories.Annotation.create_batch(7)
        annotation_service.search_annotations.return_value = annotations
        svc.BATCH_SIZE = 3
        new_url_info = {"url": sentinel.new_url}

        svc.move_annotations_by_url(url=sentinel.url, new_url_info=new_url_info)

        annotation_service.search_annotations.assert_called_once_with(
            document_uri=sentinel.url
        )
        move_annotations.assert_called_once_with(
            [annotations[-1].id], sentinel.url, new_url_info
        )
        transaction_manager.commit.assert_called_once()

        move_annotations_task.delay.assert_has_calls(
            [
                call(
                    [annotation.id for annotation in annotations[0:3]],
                    sentinel.url,
                    new_url_info,
                ),
                call(
                    [annotation.id for annotation in annotations[3:6]],
                    sentinel.url,
                    new_url_info,
                ),
            ]
        )

    def test_move_annotations_by_url_with_no_annotations(
        self, svc, annotation_service, move_annotations
    ):
        annotation_service.search_annotations.return_value = []

        svc.move_annotations_by_url(
            url=sentinel.url, new_url_info=sentinel.new_url_info
        )

        move_annotations.assert_not_called()

    @pytest.fixture(autouse=True)
    def transform_document(self, patch):
        return patch("h.services.url_migration.transform_document")

    @pytest.fixture
    def move_annotations_task(self, patch):
        return patch("h.services.url_migration.move_annotations")

    @pytest.fixture
    def move_annotations(self, svc):
        with patch.object(svc, "move_annotations") as move_annotations:
            yield move_annotations

    @pytest.fixture
    def transaction_manager(self):
        return Mock(spec_set=["commit"])

    @pytest.fixture
    def svc(self, annotation_service, transaction_manager):
        return URLMigrationService(
            transaction_manager=transaction_manager,
            annotation_service=annotation_service,
        )
