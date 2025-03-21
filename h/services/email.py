# noqa: A005

import smtplib
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import pyramid_mailer
import pyramid_mailer.message
from pyramid.request import Request
from pyramid_mailer import IMailer

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

    @property
    def message(self) -> pyramid_mailer.message.Message:
        return pyramid_mailer.message.Message(
            subject=self.subject,
            recipients=self.recipients,
            body=self.body,
            html=self.html,
            extra_headers={"X-MC-Tags": self.tag},
        )


@dataclass(frozen=True)
class LogData:
    tag: EmailTag
    sender_id: int
    recipient_ids: list[int] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def extra_msg(self) -> str:
        return ", ".join(f"{k}={v!r}" for k, v in self.extra.items() if v is not None)


class EmailService:
    """A service for sending emails."""

    def __init__(self, request: Request, mailer: IMailer) -> None:
        self._request = request
        self._mailer = mailer

    def send(self, email_data: EmailData, log_data: LogData) -> None:
        if self._request.debug:  # pragma: no cover
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

        separator = ", " if log_data.extra_msg else ""
        logger.info(
            "Sent email: tag=%r, sender_id=%s, recipient_ids=%s%s%s",
            log_data.tag,
            log_data.sender_id,
            log_data.recipient_ids,
            separator,
            log_data.extra_msg,
        )


def factory(_context, request: Request) -> EmailService:
    mailer = pyramid_mailer.get_mailer(request)
    return EmailService(request, mailer)
