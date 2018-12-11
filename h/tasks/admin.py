# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h import models
from h.celery import celery
from h.celery import get_task_logger


log = get_task_logger(__name__)


@celery.task
def rename_user(user_id, new_username):
    user = celery.request.db.query(models.User).get(user_id)
    if user is None:
        raise ValueError("Could not find user with id %d" % user_id)

    svc = celery.request.find_service(name="rename_user")
    svc.rename(user, new_username)
