# -*- coding: utf-8 -*-
"""
A module for sending email.

This module defines a Celery task for sending emails in a worker process.
"""

import pyramid_mailer
import pyramid_mailer.message

from h.celery import celery

__all__ = ('send',)


@celery.task
def send(recipients, subject, body, html=None):
    """
    Send an email.

    :param recipients: the list of email addresses to send the email to
    :type recipients: list of unicode strings

    :param subject: the subject of the email
    :type subject: unicode

    :param body: the body of the email
    :type body: unicode
    """
    email = pyramid_mailer.message.Message(subject=subject,
                                           recipients=recipients,
                                           body=body,
                                           html=html)
    pyramid_mailer.get_mailer(celery.request).send_immediately(email)
