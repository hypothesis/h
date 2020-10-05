import pytest

from h.tasks.job_queue import sync_annotations


class TestSyncAnnotations:
    def test_it(self, job_queue):
        sync_annotations()

        job_queue.sync_annotations.assert_called_once_with()

    @pytest.fixture(autouse=True)
    def celery(self, patch, pyramid_request):
        celery = patch("h.tasks.job_queue.celery")
        celery.request = pyramid_request
        return celery


pytestmark = pytest.mark.usefixtures("job_queue")
