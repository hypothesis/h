from dataclasses import asdict
from datetime import datetime, timedelta
from unittest.mock import sentinel

import pytest
from sqlalchemy import select

from h.models import TaskDone
from h.models.notification import EmailTag
from h.services.task_done import TaskData, TaskDoneService, factory


class TestTaskDoneService:
    def test_create(self, task_done_service, db_session):
        task_data = TaskData(
            tag=EmailTag.TEST,
            sender_id=123,
            recipient_ids=[124],
        )

        task_done_service.create(task_data)

        task_dones = db_session.execute(select(TaskDone)).scalars().all()
        assert len(task_dones) == 1
        assert task_dones[0].data == asdict(task_data)

    def test_sender_mention_count(self, task_done_service, factories):
        task_data = TaskData(
            tag=EmailTag.MENTION_NOTIFICATION,
            sender_id=123,
            recipient_ids=[124],
        )
        created = datetime.fromisoformat("2023-05-04 12:12:01+00:00")
        _task_done = factories.TaskDone(created=created, data=asdict(task_data))

        after = created - timedelta(seconds=1)
        assert task_done_service.sender_mention_count(task_data.sender_id, after) == 1

    @pytest.fixture
    def task_done_service(self, pyramid_request):
        return TaskDoneService(session=pyramid_request.db)


class TestFactory:
    def test_it(self, pyramid_request, TaskDoneService):
        service = factory(sentinel.context, pyramid_request)

        TaskDoneService.assert_called_once_with(session=pyramid_request.db)

        assert service == TaskDoneService.return_value

    @pytest.fixture(autouse=True)
    def TaskDoneService(self, patch):
        return patch("h.services.task_done.TaskDoneService")
