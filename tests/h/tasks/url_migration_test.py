from unittest.mock import sentinel

import pytest

from h.tasks.url_migration import move_annotations, move_annotations_by_url


class TestURLMigrationTasks:
    def test_move_annotations_by_url(self, url_migration_service):
        move_annotations_by_url(sentinel.old_url, sentinel.new_url_info)

        url_migration_service.move_annotations_by_url.assert_called_once_with(
            sentinel.old_url, sentinel.new_url_info
        )

    def test_move_annotations(self, url_migration_service):
        move_annotations(
            sentinel.annotation_ids, sentinel.current_uri_normalized, sentinel.url_info
        )

        url_migration_service.move_annotations.assert_called_once_with(
            sentinel.annotation_ids, sentinel.current_uri_normalized, sentinel.url_info
        )

    @pytest.fixture(autouse=True)
    def celery(self, patch, pyramid_request):
        celery = patch("h.tasks.url_migration.celery")
        celery.request = pyramid_request
        return celery
