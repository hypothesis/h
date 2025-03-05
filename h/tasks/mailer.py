"""
A module for sending email.

This module defines a Celery task for sending emails in a worker process.
"""

from h.services.email import EmailService, EmailTag
from h.tasks.celery import celery

__all__ = ("send",)


@celery.task(
    bind=True,
    acks_late=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_jitter=False,
)
def send(  # noqa: PLR0913
    self,  # noqa: ARG001
    recipients: list[str],
    subject: str,
    body: str,
    tag: EmailTag,
    html: str | None = None,
) -> None:
    """
    Send an email.

    :param recipients: the list of email addresses to send the email to
    :type recipients: list of unicode strings

    :param subject: the subject of the email
    :type subject: unicode

    :param body: the body of the email
    :type body: unicode
    """
    service = celery.request.find_service(EmailService)
    service.send(recipients=recipients, subject=subject, body=body, html=html, tag=tag)
