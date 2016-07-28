# -*- coding: utf-8 -*-

import logging

from h.celery import celery

from memex import storage
from memex.search.index import index
from memex.search.index import delete
from memex.search.index import reindex

__all__ = (
    'add_annotation',
    'delete_annotation',
    'reindex_annotations',
)


log = logging.getLogger(__name__)


@celery.task
def add_annotation(id_):
    annotation = storage.fetch_annotation(celery.request.db, id_)
    if annotation:
        index(celery.request.es, annotation, celery.request)


@celery.task
def delete_annotation(id_):
    delete(celery.request.es, id_)


@celery.task
def reindex_annotations():
    reindex(celery.request.db, celery.request.es, celery.request)


def subscribe_annotation_event(event):
    if event.action in ['create', 'update']:
        add_annotation.delay(event.annotation_id)
    elif event.action == 'delete':
        delete_annotation.delay(event.annotation_id)


def includeme(config):
    config.add_subscriber('h.indexer.subscribe_annotation_event',
                          'memex.events.AnnotationEvent')
