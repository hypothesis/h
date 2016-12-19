# -*- coding: utf-8 -*-

from h.celery import celery

from memex import storage
from memex.search.index import index
from memex.search.index import delete


@celery.task
def add_annotation(id_):
    annotation = storage.fetch_annotation(celery.request.db, id_)
    if annotation:
        index(celery.request.es, annotation, celery.request)


@celery.task
def delete_annotation(id_):
    delete(celery.request.es, id_)
