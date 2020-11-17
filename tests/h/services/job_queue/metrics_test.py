import datetime
from unittest import mock

import pytest

from h.services.job_queue.metrics import JobQueueMetrics, factory


class TestJobQueue:
    def test_metrics_queue_length(self, factories, job_queue_metrics):
        now = datetime.datetime.utcnow()
        one_minute = datetime.timedelta(minutes=1)

        class JobFactory(factories.Job):
            name = "name_1"
            scheduled_at = now - one_minute
            priority = 1
            tag = "tag_1"

        JobFactory()
        JobFactory(name="name_2", scheduled_at=now + one_minute)
        JobFactory(tag="tag_2")
        JobFactory(priority=2)
        JobFactory(expires_at=now - one_minute)

        metrics = job_queue_metrics.metrics()

        assert sorted(metrics) == [
            ("Custom/JobQueue/Count/Expired", 1),
            ("Custom/JobQueue/Count/Name/name_1/Tag/tag_1", 2),
            ("Custom/JobQueue/Count/Name/name_1/Tag/tag_2", 1),
            ("Custom/JobQueue/Count/Name/name_1/Total", 3),
            ("Custom/JobQueue/Count/Name/name_2/Tag/tag_1", 1),
            ("Custom/JobQueue/Count/Name/name_2/Total", 1),
            ("Custom/JobQueue/Count/Priority/1", 3),
            ("Custom/JobQueue/Count/Priority/2", 1),
            ("Custom/JobQueue/Count/Total", 4),
        ]

    @pytest.fixture
    def job_queue_metrics(self, db_session):
        return JobQueueMetrics(db_session)


class TestFactory:
    def test_it(self, pyramid_request):
        factory(mock.sentinel.context, pyramid_request)
