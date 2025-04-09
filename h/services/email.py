# noqa: A005

import smtplib
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any

import pyramid_mailer
import pyramid_mailer.message
from pyramid.request import Request
from pyramid_mailer import IMailer
from sqlalchemy.orm import Session

from h.models import TaskDone
from h.tasks.celery import get_task_logger

logger = get_task_logger(__name__)


class EmailTag(StrEnum):
    ACTIVATION = "activation"
    FLAG_NOTIFICATION = "flag_notification"
    REPLY_NOTIFICATION = "reply_notification"
    RESET_PASSWORD = "reset_password"  # noqa: S105
    MENTION_NOTIFICATION = "mention_notification"
    TEST = "test"


@dataclass(frozen=True)
class EmailData:
    recipients: list[str]
    subject: str
    body: str
    tag: EmailTag
    html: str | None = None
    subaccount: str | None = None

    @property
    def message(self) -> pyramid_mailer.message.Message:
        extra_headers = {"X-MC-Tags": self.tag}
        if self.subaccount:
            extra_headers["X-MC-Subaccount"] = self.subaccount
        return pyramid_mailer.message.Message(
            subject=self.subject,
            recipients=self.recipients,
            body=self.body,
            html=self.html,
            extra_headers=extra_headers,
        )


@dataclass(frozen=True)
class TaskData:
    tag: EmailTag
    sender_id: int
    recipient_ids: list[int] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def formatted_extra(self) -> str:
        return ", ".join(f"{k}={v!r}" for k, v in self.extra.items() if v is not None)


class EmailService:
    """A service for sending emails."""

    def __init__(self, debug: bool, session: Session, mailer: IMailer) -> None:  # noqa: FBT001
        self._debug = debug
        self._session = session
        self._mailer = mailer

    def send(self, email_data: EmailData, task_data: TaskData) -> None:
        if self._debug:  # pragma: no cover
            logger.info("emailing in debug mode: check the `mail/` directory")
        try:
            self._mailer.send_immediately(email_data.message)
        except smtplib.SMTPRecipientsRefused as exc:  # pragma: no cover
            logger.warning(
                "Recipient was refused when trying to send an email. Does the user have an invalid email address?",
                exc_info=exc,
            )
        except smtplib.SMTPException:
            raise

        separator = ", " if task_data.extra else ""
        logger.info(
            "Sent email: tag=%r, sender_id=%s, recipient_ids=%s%s%s",
            task_data.tag,
            task_data.sender_id,
            task_data.recipient_ids,
            separator,
            task_data.formatted_extra,
        )
        self._create_task_done(task_data)

    def _create_task_done(self, task_data: TaskData) -> None:
        task_done = TaskDone(data=asdict(task_data))
        self._session.add(task_done)


def factory(_context, request: Request) -> EmailService:
    mailer = pyramid_mailer.get_mailer(request)
    return EmailService(debug=request.debug, session=request.db, mailer=mailer)
