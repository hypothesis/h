"""
A module for sending email.

This module defines a Celery task for sending emails in a worker process.
"""  # noqa: A005

from typing import Any

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
def send(self, data: dict[str, Any]) -> None:  # noqa: ARG001
    """Send an email.

    :param data: A dictionary containing email data compatible with EmailData class.
    """
    service: EmailService = celery.request.find_service(EmailService)
    email_data = EmailData(**data)
    service.send(email_data)
