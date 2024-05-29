# pylint: disable=no-member # Instance of 'Celery' has no 'request' member
from datetime import datetime

import newrelic
from sqlalchemy import func, select

from h import models
from h.celery import celery, get_task_logger

log = get_task_logger(__name__)


@celery.task
def purge_deleted_annotations():
    celery.request.find_service(name="annotation_delete").bulk_delete()


@celery.task
def report_num_deleted_annotations():
    """
    Report the number of deleted annotations to New Relic.

    Send a custom metric to New Relic that counts the number of annotations
    that have been marked as deleted in the database but not yet "purged" (i.e.
    actually deleted) from the database by the purge_deleted_annotations() task
    above

    This is so that we can set a New Relic alert based on this metric so that
    we can know if the purge_deleted_annotations() task is unable to keep up
    (since it only deletes up to a limited number of annotations per task run)
    and we're failing to actually purge data from the database when users ask
    us to. Otherwise annotations could be marked as deleted but never actually
    purged and we'd never know.
    """
    newrelic.agent.record_custom_metric(
        "Custom/Annotations/MarkedAsDeleted",
        celery.request.db.scalar(
            select(
                func.count(models.Annotation.id)  # pylint:disable=not-callable
            ).where(models.Annotation.deleted.is_(True))
        ),
    )


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


@celery.task
def purge_deleted_users():
    """Remove data belonging to deleted users."""
    celery.request.find_service(name="user_delete").purge_deleted_users()
