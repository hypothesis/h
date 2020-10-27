from unittest import mock
from unittest.mock import sentinel

import pytest
from h_matchers import Any

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

        search_index._queue.add_between_times.assert_called_once_with(
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

        search_index._queue.add_by_user.assert_called_once_with(
            sentinel.userid,
            sentinel.tag,
            force=sentinel.force,
            schedule_in=sentinel.schedule_in,
        )


class TestSyncAnnotations:
    def test_it(self, search_index):
        indexer.sync_annotations("test_queue")

        search_index.sync.assert_called_once_with("test_queue")


class TestReportSyncAnnotationsQueueLength:
    def test_it(self, newrelic, search_index):
        indexer.report_sync_annotations_queue_length()

        search_index._queue.count.assert_called_once_with(
            ["storage.create_annotation", "storage.update_annotation"]
        )
        newrelic.agent.record_custom_metric.assert_called_once_with(
            Any.string(), search_index._queue.count.return_value
        )


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
