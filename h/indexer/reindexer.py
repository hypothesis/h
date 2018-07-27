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


def reindex(session, es, request):
    """Reindex all annotations into a new index, and update the alias."""

    current_index = get_aliased_index(es)
    if current_index is None:
        raise RuntimeError('cannot reindex if current index is not aliased')

    settings = request.find_service(name='settings')

    # Preload userids of shadowbanned users.
    nipsa_svc = request.find_service(name='nipsa')
    nipsa_svc.fetch_all_flagged_userids()

    new_index = configure_index(es)
    log.info('configured new index {}'.format(new_index))
    setting_name = 'reindex.new_es6_index'
    if es.version < (2,):
        setting_name = 'reindex.new_index'

    try:
        settings.put(setting_name, new_index)
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
        settings.delete(setting_name)
        request.tm.commit()
