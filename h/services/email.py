# noqa: A005

import smtplib
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
    TEST = "test"


class EmailService:
    """A service for sending emails."""

    def __init__(self, request: Request, mailer: IMailer) -> None:
        self._request = request
        self._mailer = mailer

    def send(
        self,
        recipients: list[str],
        subject: str,
        body: str,
        tag: EmailTag,
        html: str | None = None,
    ) -> None:
        extra_headers = {"X-MC-Tags": tag}
        email = pyramid_mailer.message.Message(
            subject=subject,
            recipients=recipients,
            body=body,
            html=html,
            extra_headers=extra_headers,
        )
        if self._request.debug:  # pragma: no cover
            logger.info("emailing in debug mode: check the `mail/` directory")
        try:
            self._mailer.send_immediately(email)
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
