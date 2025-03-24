# noqa: A005

import smtplib
from dataclasses import dataclass
from enum import StrEnum

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
    id: str | None = None
    """Message ID to set in Message-ID header"""
    parent_id: str | None = None
    """
    Parent message ID to be set in In-Reply-To and References headers.
    Defaults to `id`
    """

    @property
    def message(self) -> pyramid_mailer.message.Message:
        extra_headers = {"X-MC-Tags": self.tag}
        parent_id = self.parent_id if self.parent_id is not None else self.id

        if self.id:
            extra_headers["Message-ID"] = self.id

        if parent_id:
            extra_headers["In-Reply-To"] = parent_id
            extra_headers["References"] = parent_id

        return pyramid_mailer.message.Message(
            subject=self.subject,
            recipients=self.recipients,
            body=self.body,
            html=self.html,
            extra_headers=extra_headers,
        )


class EmailService:
    """A service for sending emails."""

    def __init__(self, request: Request, mailer: IMailer) -> None:
        self._request = request
        self._mailer = mailer

    def send(self, email: EmailData) -> None:
        if self._request.debug:  # pragma: no cover
            logger.info("emailing in debug mode: check the `mail/` directory")
        try:
            self._mailer.send_immediately(email.message)
        except smtplib.SMTPRecipientsRefused as exc:  # pragma: no cover
            logger.warning(
                "Recipient was refused when trying to send an email. Does the user have an invalid email address?",
                exc_info=exc,
            )
        except smtplib.SMTPException:
            raise


def factory(_context, request: Request) -> EmailService:
    mailer = pyramid_mailer.get_mailer(request)
    return EmailService(request, mailer)
