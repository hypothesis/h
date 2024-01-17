from unittest import mock
from unittest.mock import sentinel

import pytest

from h.tasks import job_queue


class TestAddAnnotationsBetweenTimes:
    def test_it(self, queue_service):
        job_queue.add_annotations_between_times(
            sentinel.name, sentinel.start_time, sentinel.end_time, sentinel.tag
        )

        queue_service.add_between_times.assert_called_once_with(
            sentinel.name, sentinel.start_time, sentinel.end_time, sentinel.tag
        )


class TestAddAnnotationsFromUser:
    def test_it(self, queue_service):
        job_queue.add_annotations_from_user(
            sentinel.name,
            sentinel.userid,
            sentinel.tag,
            force=sentinel.force,
            schedule_in=sentinel.schedule_in,
        )

        queue_service.add_by_user.assert_called_once_with(
            sentinel.name,
            sentinel.userid,
            sentinel.tag,
            force=sentinel.force,
            schedule_in=sentinel.schedule_in,
        )


class TestAddAnnotationsFromGroup:
    def test_it(self, queue_service):
        job_queue.add_annotations_from_group(
            sentinel.name,
            sentinel.groupid,
            sentinel.tag,
            force=sentinel.force,
            schedule_in=sentinel.schedule_in,
        )

        queue_service.add_by_group.assert_called_once_with(
            sentinel.name,
            sentinel.groupid,
            sentinel.tag,
            force=sentinel.force,
            schedule_in=sentinel.schedule_in,
        )


@pytest.fixture(autouse=True)
def celery(patch, pyramid_request):
    cel = patch("h.tasks.job_queue.celery")
    cel.request = pyramid_request
    return cel


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.es = mock.Mock()
    return pyramid_request
