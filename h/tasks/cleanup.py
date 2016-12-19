# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from datetime import datetime

from h import models
from h.celery import celery
from h.celery import get_task_logger


log = get_task_logger(__name__)


@celery.task
def purge_expired_auth_tickets():
    celery.request.db.query(models.AuthTicket) \
        .filter(models.AuthTicket.expires < datetime.utcnow()) \
        .delete()


@celery.task
def purge_expired_tokens():
    celery.request.db.query(models.Token) \
        .filter(models.Token.expires < datetime.utcnow()) \
        .delete()
