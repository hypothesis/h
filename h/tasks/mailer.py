"""
A module for sending email.

This module defines a Celery task for sending emails in a worker process.
"""

from h.services.email import EmailData, EmailService
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
def send(self, email: EmailData) -> None:  # noqa: ARG001
    """Send an email.

    :param email: The email data to send.
    """
    service = celery.request.find_service(EmailService)
    service.send(email)
