# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging

from h.search.config import (
    configure_index,
    get_aliased_index,
    update_aliased_index,
)
from h.search.index import BatchIndexer

log = logging.getLogger(__name__)

SETTING_NEW_INDEX = 'reindex.new_index'
SETTING_NEW_ES6_INDEX = 'reindex.new_es6_index'


def reindex(session, es, request):
    """Reindex all annotations into a new index, and update the alias."""

    if get_aliased_index(es) is None:
        raise RuntimeError('cannot reindex if current index is not aliased')

    settings = request.find_service(name='settings')

    new_index = configure_index(es)
    if es.using_es6:
        setting_name = SETTING_NEW_ES6_INDEX
    else:
        setting_name = SETTING_NEW_INDEX

    try:
        settings.put(setting_name, new_index)
        request.tm.commit()

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

    finally:
        settings.delete(setting_name)
        request.tm.commit()
