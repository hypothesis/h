from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from pyramid.request import Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import count

from h.models import TaskDone
from h.models.notification import EmailTag


@dataclass(frozen=True)
class TaskData:
    tag: EmailTag
    sender_id: int
    recipient_ids: list[int] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def formatted_extra(self) -> str:
        return ", ".join(f"{k}={v!r}" for k, v in self.extra.items() if v is not None)


class TaskDoneService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, task_data: TaskData) -> None:
        task_done = TaskDone(data=asdict(task_data))
        self._session.add(task_done)

    def sender_mention_count(self, sender_id: int, after: datetime) -> int:
        stmt = select(count(TaskDone.id)).where(
            TaskDone.data["sender_id"].astext == str(sender_id),
            TaskDone.created >= after,
        )
        return self._session.execute(stmt).scalar_one()


def factory(_context, request: Request) -> TaskDoneService:
    return TaskDoneService(session=request.db)
