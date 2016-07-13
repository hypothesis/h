# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.celery import celery
from h.celery import get_task_logger


log = get_task_logger(__name__)


@celery.task
def rename_user(old_username, new_username):
    svc = celery.request.find_service(name='rename_user')
    svc.rename(old_username, new_username)
