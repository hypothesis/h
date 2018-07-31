# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging

from celery.result import ResultSet

from h.models import Annotation
from h.search.config import (
    configure_index,
    delete_index,
    get_aliased_index,
    update_aliased_index,
)
from h.search.index import BatchIndexer
from h.tasks.indexer import reindex_annotations

log = logging.getLogger(__name__)


def reindex(session, es, request, parallel=False):
    """
    Reindex all annotations into a new index, and update the alias.

    :param parallel: If `True`, reindex annotations into the new index in batches
                     using Celery tasks.
    """

    current_index = get_aliased_index(es)
    if current_index is None:
        raise RuntimeError('cannot reindex if current index is not aliased')

    settings = request.find_service(name='settings')

    new_index = configure_index(es)
    log.info('configured new index {}'.format(new_index))
    setting_name = 'reindex.new_es6_index'
    if es.version < (2,):
        setting_name = 'reindex.new_index'

    try:
        settings.put(setting_name, new_index)
        request.tm.commit()

        if parallel:
            log.info('reindexing annotations into new index {}'.format(new_index))
            _parallel_reindex(request.db, batch_size=2000, max_active_tasks=10, timeout=60)
        else:
            log.info('reindexing annotations into new index {}'.format(new_index))
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

        log.info('making new index {} current'.format(new_index))
        update_aliased_index(es, new_index)

        log.info('removing previous index {}'.format(current_index))
        delete_index(es, current_index)

    finally:
        settings.delete(setting_name)
        request.tm.commit()


def _parallel_reindex(session, batch_size, max_active_tasks, timeout=None):
    """
    Use Celery to reindex batches of annotations in parallel.

    :param batch_size: Number of annotations to index per Celery task.
    :param max_active_tasks: Maximum number of tasks to create before waiting
                             for active tasks to complete.
    :param timeout: Max delay in seconds to wait for a batch of tasks to finish.
    """

    rs = ResultSet([])
    completed_tasks = 0

    for batch_ids in _annotation_ids_batched_by_date(session, batch_size):

        task_result = reindex_annotations.delay(batch_ids)
        rs.add(task_result)

        if len(rs.results) >= max_active_tasks:
            # Block until at least one active task has finished.
            next(rs.iter_native())
            completed_tasks += rs.completed_count()

            # Remove completed tasks from tracked set.
            for result in rs.results:
                if result.ready():
                    rs.remove(result)

            log.info('indexed {} annotations'.format(completed_tasks * batch_size))

    log.info('waiting for remaining reindexing tasks')
    rs.join(timeout=timeout)


def _annotation_ids_batched_by_date(session, batch_size=100):
    """Yield batches of annotation IDs to reindex."""

    ann_ids = (session.query(Annotation.id)
                      .filter_by(deleted=False)
                      .order_by(Annotation.updated)
                      .yield_per(batch_size))

    batch = []
    for (ann_id,) in ann_ids:
        batch.append(ann_id)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:
        yield batch
