# -*- coding: utf-8 -*-

from h import storage
from h.celery import celery
from h.indexer.reindexer import SETTING_NEW_INDEX

from memex.search.index import index
from memex.search.index import delete


@celery.task
def add_annotation(id_):
    annotation = storage.fetch_annotation(celery.request.db, id_)
    if annotation:
        index(celery.request.es, annotation, celery.request)

        # If a reindex is running at the moment, add annotation to the new index
        # as well.
        future_index = _current_reindex_new_name(celery.request)
        if future_index is not None:
            index(celery.request.es, annotation, celery.request,
                  target_index=future_index)


@celery.task
def delete_annotation(id_):
    delete(celery.request.es, id_)

    # If a reindex is running at the moment, delete annotation from the
    # new index as well.
    future_index = _current_reindex_new_name(celery.request)
    if future_index is not None:
        delete(celery.request.es, id_, target_index=future_index)


def _current_reindex_new_name(request):
    settings = celery.request.find_service(name='settings')
    new_index = settings.get(SETTING_NEW_INDEX)

    return new_index
