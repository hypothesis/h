"""
A module for sending email.

This module defines a Celery task for sending emails in a worker process.
"""

import smtplib

from h.services.email import EmailData, EmailService, EmailTag
from h.tasks.celery import celery, get_task_logger

__all__ = ("send",)

logger = get_task_logger(__name__)


@celery.task(bind=True, max_retries=3, acks_late=True, serializer="pickle")
def send(  # noqa: PLR0913
    self,
    recipients: list[str] | EmailData,
    subject: str | None = None,
    body: str | None = None,
    tag: EmailTag | None = None,
    html: str | None = None,
) -> None:
    """Send an email.

    :param recipients: the list of email addresses to send to or an EmailData object
    :param subject: the email subject
    :param body: the email body
    :param tag: the email tag
    :param html: HTML version of the email
    """
    service = celery.request.find_service(EmailService)

    if isinstance(recipients, EmailData):
        email_data = recipients
    else:
        email_data = EmailData(
            recipients=recipients,
            subject=subject,
            body=body,
            tag=tag,
            html=html,
        )

    try:
        service.send(email_data)
    except smtplib.socket.error as exc:
        # Exponential backoff in case the SMTP service is having problems.
        countdown = self.default_retry_delay * 2**self.request.retries
        self.retry(exc=exc, countdown=countdown)
