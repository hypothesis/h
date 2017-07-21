# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from datetime import datetime, timedelta

from h import models
from h.celery import celery
from h.celery import get_task_logger


log = get_task_logger(__name__)


@celery.task
def purge_deleted_annotations():
    """
    Remove annotations marked as deleted from the database.

    Deletes all annotations flagged as deleted more than 10 minutes ago. This
    buffer period should ensure that this task doesn't delete annotations
    deleted just before the task runs, which haven't yet been processed by the
    streamer.
    """
    cutoff = datetime.utcnow() - timedelta(minutes=10)
    celery.request.db.query(models.Annotation) \
        .filter_by(deleted=True) \
        .filter(models.Annotation.updated < cutoff) \
        .delete()


@celery.task
def purge_expired_auth_tickets():
    celery.request.db.query(models.AuthTicket) \
        .filter(models.AuthTicket.expires < datetime.utcnow()) \
        .delete()


@celery.task
def purge_expired_authz_codes():
    celery.request.db.query(models.AuthzCode) \
        .filter(models.AuthzCode.expires < datetime.utcnow()) \
        .delete()


@celery.task
def purge_expired_tokens():
    celery.request.db.query(models.Token) \
        .filter(models.Token.expires < datetime.utcnow()) \
        .delete()


@celery.task
def purge_removed_features():
    """Remove old feature flags from the database."""
    models.Feature.remove_old_flags(celery.request.db)
