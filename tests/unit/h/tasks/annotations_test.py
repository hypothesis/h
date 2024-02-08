import pytest

from h.tasks.annotations import sync_annotation_slim


class TestSyncAnnotationSlim:
    AUTHORITY_1 = "AUTHORITY_1"
    AUTHORITY_2 = "AUTHORITY_2"

    USERNAME_1 = "USERNAME_1"
    USERNAME_2 = "USERNAME_2"

    def test_it(self, factories, annotation_write_service, queue_service):
        annotation = factories.Annotation()
        # Some deleted annotations that should not be processed
        factories.Annotation.create_batch(10, deleted=True)
        job = factories.SyncAnnotationJob(annotation=annotation, name="annotation_slim")

        queue_service.get.return_value = [job]

        sync_annotation_slim(1)

        queue_service.get.assert_called_once_with(name="annotation_slim", limit=1)
        annotation_write_service.upsert_annotation_slim.assert_called_once_with(
            annotation
        )
        queue_service.delete.assert_called_once_with([job])

    def test_job_for_missing_annotation(
        self, factories, annotation_write_service, queue_service, db_session
    ):
        annotation = factories.Annotation()
        job = factories.SyncAnnotationJob(annotation=annotation, name="annotation_slim")
        db_session.delete(annotation)
        db_session.commit()

        queue_service.get.return_value = [job]

        sync_annotation_slim(1)

        queue_service.get.assert_called_once_with(name="annotation_slim", limit=1)
        annotation_write_service.upsert_annotation_slim.assert_not_called()
        queue_service.delete.assert_called_once_with([job])

    def test_it_with_no_pending_jobs(self, queue_service, annotation_write_service):
        queue_service.get.return_value = []

        sync_annotation_slim(1)

        annotation_write_service.upsert_annotation_slim.assert_not_called()

    @pytest.fixture(autouse=True)
    def celery(self, patch, pyramid_request):
        cel = patch("h.tasks.annotations.celery", autospec=False)
        cel.request = pyramid_request
        return cel
