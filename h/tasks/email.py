"""
A module for sending email.

This module defines a Celery task for sending emails in a worker process.
"""  # noqa: A005

from typing import Any

from h.services.email import EmailData, EmailService, LogData
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
def send(
    self,  # noqa: ARG001
    email_data: dict[str, Any],
    log_data: dict[str, Any],
) -> None:
    """Send an email.

    :param email_data: A dictionary containing email data compatible with EmailData class.
    :param log_data: A dictionary containing log data compatible with LogData class.
    """
    service: EmailService = celery.request.find_service(EmailService)
    service.send(EmailData(**email_data), LogData(**log_data))
