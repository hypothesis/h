# -*- coding: utf-8 -*-
"""
A module for sending email.

This module defines a Celery task for sending emails in a worker process.
"""
from __future__ import unicode_literals

import smtplib

import pyramid_mailer
import pyramid_mailer.message

from h.celery import celery, get_task_logger

__all__ = ("send",)

log = get_task_logger(__name__)


@celery.task(bind=True, max_retries=3)
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
    email = pyramid_mailer.message.Message(
        subject=subject, recipients=recipients, body=body, html=html
    )
    mailer = pyramid_mailer.get_mailer(celery.request)
    try:
        if celery.request.debug:
            log.info("emailing in debug mode: check the `mail/' directory")
        mailer.send_immediately(email)
    except smtplib.SMTPRecipientsRefused as exc:
        log.warning(
            "Recipient was refused when trying to send an email. Does the user have an invalid email address?",
            exc_info=exc,
        )
    except (smtplib.socket.error, smtplib.SMTPException) as exc:
        # Exponential backoff in case the SMTP service is having problems.
        countdown = self.default_retry_delay * 2 ** self.request.retries
        self.retry(exc=exc, countdown=countdown)
