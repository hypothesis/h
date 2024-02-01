from h.celery import celery
from h.services import UserExpungeService


@celery.task
def expunge_deleted_users():
    """Incrementally expunge deleted users and their data."""
    request = celery.request  # pylint:disable=no-member

    request.find_service(UserExpungeService).expunge_deleted_users()
