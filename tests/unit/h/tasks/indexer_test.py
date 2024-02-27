from collections import Counter
from unittest import mock
from unittest.mock import sentinel

import pytest

from h.services.job_queue_metrics import JobQueueMetrics
from h.tasks import indexer

pytestmark = pytest.mark.usefixtures("search_index")


class TestSearchIndexServicesWrapperTasks:
    """Tests for tasks that just wrap SearchIndexServices functions."""

    def test_add_annotation(self, search_index):
        indexer.add_annotation(sentinel.annotation_id)

        search_index.add_annotation_by_id.assert_called_once_with(
            sentinel.annotation_id
        )

    def test_delete_annotation(self, search_index):
        indexer.delete_annotation(sentinel.annotation_id)

        search_index.delete_annotation_by_id.assert_called_once_with(
            sentinel.annotation_id
        )


class TestSyncAnnotations:
    def test_it(self, newrelic, log, annotation_sync_service):
        indexer.sync_annotations("test_queue")

        annotation_sync_service.sync.assert_called_once_with("test_queue")
        log.info.assert_called_once_with(annotation_sync_service.sync.return_value)
        newrelic.agent.record_custom_metrics.assert_called_once_with(
            [
                ("Custom/SyncAnnotations/Queue/foo", 2),
                ("Custom/SyncAnnotations/Queue/bar", 3),
            ]
        )

    @pytest.fixture
    def log(self, patch):
        return patch("h.tasks.indexer.log")

    @pytest.fixture
    def annotation_sync_service(self, annotation_sync_service):
        annotation_sync_service.sync.return_value = Counter({"foo": 2, "bar": 3})
        return annotation_sync_service


class TestReportJobQueueMetrics:
    def test_it(self, job_queue_metrics, newrelic):
        indexer.report_job_queue_metrics()

        newrelic.agent.record_custom_metrics.assert_called_once_with(
            job_queue_metrics.metrics.return_value
        )

    @pytest.fixture(autouse=True)
    def job_queue_metrics(self, pyramid_config):
        job_queue_metrics = mock.create_autospec(
            JobQueueMetrics, spec_set=True, instance=True
        )
        pyramid_config.register_service(job_queue_metrics, name="job_queue_metrics")
        return job_queue_metrics


@pytest.fixture(autouse=True)
def celery(patch, pyramid_request):
    cel = patch("h.tasks.indexer.celery")
    cel.request = pyramid_request
    return cel


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.es = mock.Mock()
    return pyramid_request


@pytest.fixture(autouse=True)
def newrelic(patch):
    return patch("h.tasks.indexer.newrelic")
