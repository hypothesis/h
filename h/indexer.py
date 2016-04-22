# -*- coding: utf-8 -*-

from h.celery import celery

from h.api import storage
from h.api.search.index import index
from h.api.search.index import delete

__all__ = (
    'add_annotation',
    'delete_annotation',
)


@celery.task
def add_annotation(id_):
    annotation = storage.fetch_annotation(celery.request, id_)
    index(celery.request.es, annotation, celery.request)


@celery.task
def delete_annotation(id_):
    delete(celery.request.es, id_)


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
