"""
A module for sending email.

This module defines a Celery task for sending emails in a worker process.
"""

import smtplib

from h.services.email import EmailLogData, EmailService, EmailTag
from h.tasks.celery import celery

__all__ = ("send",)


@celery.task(bind=True, max_retries=3, acks_late=True)
def send(  # noqa: PLR0913
    self,
    recipients: list[str],
    subject: str,
    body: str,
    tag: EmailTag,
    html: str | None = None,
    log_data: EmailLogData | None = None,
) -> None:
    """
    Send an email.

    :param recipients: the list of email addresses to send the email to
    :param subject: the subject of the email
    :param body: the body of the email
    """
    service = celery.request.find_service(EmailService)
    try:
        service.send(
            recipients=recipients,
            subject=subject,
            body=body,
            html=html,
            tag=tag,
            log_data=log_data,
        )
    except smtplib.socket.error as exc:
        # Exponential backoff in case the SMTP service is having problems.
        countdown = self.default_retry_delay * 2**self.request.retries
        self.retry(exc=exc, countdown=countdown)
