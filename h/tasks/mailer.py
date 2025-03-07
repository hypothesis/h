"""
A module for sending email.

This module defines a Celery task for sending emails in a worker process.
"""

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
        email = recipients
    else:
        email = EmailData(
            recipients=recipients,
            subject=subject,
            body=body,
            tag=tag,
            html=html,
        )
    service.send(email)
