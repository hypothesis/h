from h import models
from h.celery import celery, get_task_logger
from h.models import Annotation
from h.search.index import BatchIndexer

log = get_task_logger(__name__)


@celery.task
def add_annotation(id_):
    search_index = celery.request.find_service(name="search_index")
    search_index.add_annotation_by_id(id_)


@celery.task
def delete_annotation(id_):
    search_index = celery.request.find_service(name="search_index")
    search_index.delete_annotation_by_id(id_)


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

    log.info("Re-index from %s to %s complete.", start_date, end_date)
