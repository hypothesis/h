# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging

from h.search.config import (
    configure_index,
    delete_index,
    get_aliased_index,
    update_aliased_index,
)
from h.search.index import BatchIndexer

log = logging.getLogger(__name__)

SETTING_NEW_INDEX = 'reindex.new_index'


def reindex(session, es, request):
    """Reindex all annotations into a new index, and update the alias."""

    current_index = get_aliased_index(es)
    if current_index is None:
        raise RuntimeError('cannot reindex if current index is not aliased')

    settings = request.find_service(name='settings')

    new_index = configure_index(es)
    log.info('configured new index {}'.format(new_index))

    try:
        settings.put(SETTING_NEW_INDEX, new_index)
        request.tm.commit()

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
        settings.delete(SETTING_NEW_INDEX)
        request.tm.commit()
