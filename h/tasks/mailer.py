"""
A module for sending email.

This module defines a Celery task for sending emails in a worker process.
"""

import smtplib

from h.services.email import EmailService
from h.tasks.celery import celery

__all__ = ("send",)


@celery.task(bind=True, max_retries=3, acks_late=True)
def send(self, recipients, subject, body, html=None):
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
    try:
        service.send(recipients=recipients, subject=subject, body=body, html=html)
    except smtplib.socket.error as exc:
        # Exponential backoff in case the SMTP service is having problems.
        countdown = self.default_retry_delay * 2**self.request.retries
        self.retry(exc=exc, countdown=countdown)
