# noqa: A005

import smtplib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pyramid_mailer
import pyramid_mailer.message
from pyramid.request import Request
from pyramid_mailer import IMailer
from sqlalchemy.orm import Session

from h.models.notification import EmailTag
from h.services.task_done import TaskData, TaskDoneService
from h.tasks.celery import get_task_logger

logger = get_task_logger(__name__)

# Limit for the number of mention emails sent by a single user in a day to prevent abuse
DAILY_SENDER_MENTION_LIMIT = 100


@dataclass(frozen=True)
class EmailData:
    recipients: list[str]
    subject: str
    body: str
    tag: EmailTag
    html: str | None = None
    subaccount: str | None = None
    reply_to: str | None = None

    @property
    def message(self) -> pyramid_mailer.message.Message:
        extra_headers: dict[str, str] = {"X-MC-Tags": self.tag}

        if self.subaccount:
            extra_headers["X-MC-Subaccount"] = self.subaccount

        if self.reply_to:  # pragma: nocover
            extra_headers["Reply-To"] = self.reply_to

        subject = " ".join(self.subject.splitlines())

        return pyramid_mailer.message.Message(
            subject=subject,
            recipients=self.recipients,
            body=self.body,
            html=self.html,
            extra_headers=extra_headers,
        )


class EmailService:
    """A service for sending emails."""

    def __init__(
        self,
        debug: bool,  # noqa: FBT001
        session: Session,
        mailer: IMailer,
        task_done_service: TaskDoneService,
    ) -> None:
        self._debug = debug
        self._session = session
        self._mailer = mailer
        self._task_done_service = task_done_service

    def send(self, email_data: EmailData, task_data: TaskData) -> None:
        if not self._allow_sending(task_data):
            return

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
        self._task_done_service.create(task_data)

    def _allow_sending(self, task_data: TaskData) -> bool:
        if (
            task_data.tag == EmailTag.MENTION_NOTIFICATION
            and self._sender_limit_reached(task_data)
        ):
            logger.warning(
                "Not sending email: tag=%r sender_id=%s recipient_ids=%s. Sender limit reached.",
                task_data.tag,
                task_data.sender_id,
                task_data.recipient_ids,
            )
            return False
        return True

    def _sender_limit_reached(self, task_data: TaskData) -> bool:
        after = datetime.now(UTC) - timedelta(days=1)
        count = self._task_done_service.sender_mention_count(task_data.sender_id, after)
        return count >= DAILY_SENDER_MENTION_LIMIT


def factory(_context, request: Request) -> EmailService:
    mailer = pyramid_mailer.get_mailer(request)
    return EmailService(
        debug=request.debug,
        session=request.db,
        mailer=mailer,
        task_done_service=request.find_service(TaskDoneService),
    )
