from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from freezegun import freeze_time
from sqlalchemy import select

from h.models import TaskDone
from h.tasks.task_done import delete_expired_rows


@freeze_time("2023-05-04 12:12:01")
def test_delete_expired_rows(db_session, factories):
    frozen_time = datetime.fromisoformat("2023-05-04 12:12:01+00:00")
    _expired_task_dones = [
        factories.TaskDone(expires_at=frozen_time - timedelta(seconds=1)),
        factories.TaskDone(expires_at=frozen_time - timedelta(seconds=2)),
    ]
    fresh_task_done = factories.TaskDone(expires_at=frozen_time + timedelta(seconds=1))

    delete_expired_rows()

    # It should have deleted expired_task_dones but not fresh_task_done.
    assert db_session.scalars(select(TaskDone.id)).all() == [fresh_task_done.id]


@pytest.fixture(autouse=True)
def celery(patch, pyramid_request):
    cel = patch("h.tasks.task_done.celery", autospec=False)
    cel.request = pyramid_request
    return cel


@pytest.fixture(autouse=True)
def pyramid_request(pyramid_request):
    pyramid_request.tm = MagicMock()
    return pyramid_request
