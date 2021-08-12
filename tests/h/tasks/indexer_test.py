from collections import Counter
from unittest import mock
from unittest.mock import sentinel

import pytest

from h.services.job_queue.metrics import JobQueueMetrics
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


class TestAddAnnotationsBetweenTimes:
    def test_it(self, search_index):
        indexer.add_annotations_between_times(
            sentinel.start_time, sentinel.end_time, sentinel.tag
        )

        search_index._queue.add_between_times.assert_called_once_with(  # pylint:disable=protected-access
            sentinel.start_time, sentinel.end_time, sentinel.tag
        )


class TestAddUsersAnnotations:
    def test_it(self, search_index):
        indexer.add_users_annotations(
            sentinel.userid,
            sentinel.tag,
            force=sentinel.force,
            schedule_in=sentinel.schedule_in,
        )

        search_index._queue.add_by_user.assert_called_once_with(  # pylint:disable=protected-access
            sentinel.userid,
            sentinel.tag,
            force=sentinel.force,
            schedule_in=sentinel.schedule_in,
        )


class TestAddGroupAnnotations:
    def test_it(self, search_index):
        indexer.add_group_annotations(
            sentinel.groupid,
            sentinel.tag,
            force=sentinel.force,
            schedule_in=sentinel.schedule_in,
        )

        search_index._queue.add_by_group.assert_called_once_with(  # pylint:disable=protected-access
            sentinel.groupid,
            sentinel.tag,
            force=sentinel.force,
            schedule_in=sentinel.schedule_in,
        )


class TestSyncAnnotations:
    def test_it(self, newrelic, log, search_index):
        indexer.sync_annotations("test_queue")

        search_index.sync.assert_called_once_with("test_queue")
        log.info.assert_called_once_with(search_index.sync.return_value)
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
    def search_index(self, search_index):
        search_index.sync.return_value = Counter({"foo": 2, "bar": 3})
        return search_index


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
