# pylint: disable=no-member # Instance of 'Celery' has no 'request' member
from datetime import datetime

from h import models
from h.celery import celery, get_task_logger

log = get_task_logger(__name__)


@celery.task
def purge_deleted_annotations():
    celery.request.find_service(name="annotation_delete").bulk_delete()


@celery.task
def purge_expired_auth_tickets():
    celery.request.db.query(models.AuthTicket).filter(
        models.AuthTicket.expires < datetime.utcnow()
    ).delete()


@celery.task
def purge_expired_authz_codes():
    celery.request.db.query(models.AuthzCode).filter(
        models.AuthzCode.expires < datetime.utcnow()
    ).delete()


@celery.task
def purge_expired_tokens():
    now = datetime.utcnow()
    celery.request.db.query(models.Token).filter(
        models.Token.expires < now, models.Token.refresh_token_expires < now
    ).delete()


@celery.task
def purge_removed_features():
    """Remove old feature flags from the database."""
    models.Feature.remove_old_flags(celery.request.db)
