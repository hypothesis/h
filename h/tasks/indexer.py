from h import models, storage
from h.celery import celery, get_task_logger
from h.models import Annotation
from h.search.index import BatchIndexer, delete, index

log = get_task_logger(__name__)


@celery.task
def add_annotation(id_):
    annotation = storage.fetch_annotation(celery.request.db, id_)
    if annotation:
        index(celery.request.es, annotation, celery.request)

        # If a reindex is running at the moment, add annotation to the new index
        # as well.
        future_index = _current_reindex_new_name(celery.request, "reindex.new_index")
        if future_index is not None:
            index(
                celery.request.es, annotation, celery.request, target_index=future_index
            )

        if annotation.is_reply:
            add_annotation.delay(annotation.thread_root_id)


@celery.task
def delete_annotation(id_):
    delete(celery.request.es, id_)

    # If a reindex is running at the moment, delete annotation from the
    # new index as well.
    future_index = _current_reindex_new_name(celery.request, "reindex.new_index")
    if future_index is not None:
        delete(celery.request.es, id_, target_index=future_index)


@celery.task
def reindex_user_annotations(userid):
    ids = [
        a.id
        for a in celery.request.db.query(models.Annotation.id).filter_by(userid=userid)
    ]

    indexer = BatchIndexer(celery.request.db, celery.request.es, celery.request)
    errored = indexer.index(ids)
    if errored:
        log.warning("Failed to re-index annotations into ES6 %s", errored)


@celery.task
def reindex_annotations_in_date_range(start_date, end_date, max_annotations=250000):
    """Re-index annotations from Postgres to Elasticsearch in a date range.

    :param start_date: Begin at this time (greater or equal)
    :param end_date: End at this time (less than or equal)
    :param max_annotations: Maximum number of items to process overall

    """
    log.info(f"Re-indexing from {start_date} to {end_date}...")

    indexer = BatchIndexer(celery.request.db, celery.request.es, celery.request)
    errored = indexer.index(
        annotation.id
        for annotation in celery.request.db.query(Annotation.id)
        .filter(Annotation.updated >= start_date)
        .filter(Annotation.updated <= end_date)
        .limit(max_annotations)
    )

    if errored:
        log.warning("Failed to re-index annotations into ES6 %s", errored)

    log.info(
        "Re-index from %s to %s complete.", start_date, end_date,
    )


def _current_reindex_new_name(request, new_index_setting_name):
    settings = celery.request.find_service(name="settings")
    new_index = settings.get(new_index_setting_name)

    return new_index
