"""
A module for sending email.

This module defines a Celery task for sending emails in a worker process.
"""

from typing import Any

from h.services.email import EmailData, EmailService, EmailTag
from h.tasks.celery import celery, get_task_logger

__all__ = ("send",)

logger = get_task_logger(__name__)


@celery.task(
    bind=True,
    acks_late=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_jitter=False,
)
def send(  # noqa: PLR0913
    self,  # noqa: ARG001
    recipients: list[str] | dict[str, Any],
    subject: str | None = None,
    body: str | None = None,
    html: str | None = None,
    tag: EmailTag | None = None,
) -> None:
    """Send an email.

    :param recipients: A list of email addresses or a dictionary with email data.
    :param subject: The subject of the email.
    :param body: The body of the email.
    :param html: The HTML body of the email.
    :param tag: An tag for the email.
    """
    if isinstance(recipients, dict):
        email = EmailData(**recipients)
    else:
        email = EmailData(
            recipients=recipients,
            subject=subject,
            body=body,
            html=html,
            tag=tag,
        )

    service: EmailService = celery.request.find_service(EmailService)
    service.send(email)
