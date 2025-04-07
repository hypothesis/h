"""Celery tasks for maintaining the task_done database table."""

from datetime import UTC, datetime

from sqlalchemy import delete

from h.models import TaskDone
from h.tasks.celery import celery


@celery.task
def delete_expired_rows():
    """Delete any expired rows from the task_done table.

    This is just so that the table doesn't grow forever.

    This is intended to be called periodically.
    """
    request = celery.request

    with request.tm:
        request.db.execute(
            delete(TaskDone).where(TaskDone.expires_at < datetime.now(UTC))
        )
