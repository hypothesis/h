# -*- coding: utf-8 -*-

import logging

from h.tasks.indexer import add_annotation, delete_annotation

from memex.search.config import (
    configure_index,
    get_aliased_index,
    update_aliased_index,
)
from memex.search.index import BatchIndexer

log = logging.getLogger(__name__)


def reindex(session, es, request):
    """Reindex all annotations into a new index, and update the alias."""

    if get_aliased_index(es) is None:
        raise RuntimeError('cannot reindex if current index is not aliased')

    new_index = configure_index(es)
    indexer = BatchIndexer(session, es, request, target_index=new_index, op_type='create')

    errored = indexer.index()
    if errored:
        log.debug('failed to index {} annotations, retrying...'.format(
            len(errored)))
        errored = indexer.index(errored)
        if errored:
            log.warn('failed to index {} annotations: {!r}'.format(
                len(errored),
                errored))

    update_aliased_index(es, new_index)


def subscribe_annotation_event(event):
    if event.action in ['create', 'update']:
        add_annotation.delay(event.annotation_id)
    elif event.action == 'delete':
        delete_annotation.delay(event.annotation_id)


def includeme(config):
    config.add_subscriber('h.indexer.subscribe_annotation_event',
                          'memex.events.AnnotationEvent')
