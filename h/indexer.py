# -*- coding: utf-8 -*-

import logging

from h.celery import celery

from h.api import storage
from h.api.search.index import index
from h.api.search.index import delete
from h.api.search.index import BatchIndexer
from h.api.search.index import BatchDeleter

__all__ = (
    'add_annotation',
    'delete_annotation',
    'reindex',
)


log = logging.getLogger(__name__)


@celery.task
def add_annotation(id_):
    annotation = storage.fetch_annotation(celery.request, id_)
    index(celery.request.es, annotation, celery.request)


@celery.task
def delete_annotation(id_):
    delete(celery.request.es, id_)


@celery.task
def reindex():
    if not celery.request.feature('postgres'):
        return

    indexing = BatchIndexer(celery.request.db, celery.request.es, celery.request)
    indexing.index_all()

    deleting = BatchDeleter(celery.request.db, celery.request.es)
    deleting.delete_all()


def subscribe_annotation_event(event):
    if not event.request.feature('postgres'):
        return

    if event.action in ['create', 'update']:
        add_annotation.delay(event.annotation_id)
    elif event.action == 'delete':
        delete_annotation.delay(event.annotation_id)


def includeme(config):
    config.add_subscriber('h.indexer.subscribe_annotation_event',
                          'h.api.events.AnnotationEvent')
