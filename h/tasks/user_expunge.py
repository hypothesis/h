from h.celery import celery


@celery.task
def expunge_deleted_users():
    """Incrementally expunge deleted users and their data."""
    request = celery.request  # pylint:disable=no-member

    request.find_service(name="user_delete").expunge_deleted_users()
