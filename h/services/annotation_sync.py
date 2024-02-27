from collections import defaultdict

from dateutil.parser import isoparse

from h.db.types import URLSafeUUID
from h.models import Annotation
from h.search.index import BatchIndexer


class Result:
    """String values for logging and metrics."""

    # These are in the style of New Relic custom metric names.
    SYNCED_MISSING = "Synced/{tag}/Missing_from_Elastic"
    SYNCED_DIFFERENT = "Synced/{tag}/Different_in_Elastic"
    SYNCED_FORCED = "Synced/{tag}/Forced"
    SYNCED_TAG_TOTAL = "Synced/{tag}/Total"
    SYNCED_TOTAL = "Synced/Total"
    COMPLETED_UP_TO_DATE = "Completed/{tag}/Up_to_date_in_Elastic"
    COMPLETED_DELETED = "Completed/{tag}/Deleted_from_db"
    COMPLETED_FORCED = "Completed/{tag}/Forced"
    COMPLETED_TAG_TOTAL = "Completed/{tag}/Total"
    COMPLETED_TOTAL = "Completed/Total"


class AnnotationSyncService:
    """A service for synchronizing annotations from Postgres to Elasticsearch."""

    def __init__(self, batch_indexer, db, es, queue_service):
        self._batch_indexer = batch_indexer
        self._db = db
        self._es = es
        self._queue_service = queue_service

    def sync(self, limit):
        """
        Synchronize a batch of annotations from Postgres to Elasticsearch.

        Called periodically by a Celery task (see h-periodic).

        Each time this method runs it considers a fixed number of sync
        annotation jobs from the queue and for each job:

        * If the annotation is already the same in Elastic as in the DB then
          remove the job from the queue

        * If the annotation is missing from Elastic or different in Elastic
          than in the DB then re-sync the annotation into Elastic. Leave the
          job on the queue to be re-checked and removed the next time the
          method runs.
        """
        jobs = self._queue_service.get(name="sync_annotation", limit=limit)

        if not jobs:
            return {}

        counts = defaultdict(set)

        annotation_ids = {
            URLSafeUUID.hex_to_url_safe(job.kwargs["annotation_id"])
            for job in jobs
            if not job.kwargs.get("force", False)
        }
        if annotation_ids:
            annotations_from_db = self._get_annotations_from_db(annotation_ids)
            annotations_from_es = self._get_annotations_from_es(annotation_ids)
        else:
            annotations_from_db = {}
            annotations_from_es = {}

        # Completed jobs that can be removed from the queue.
        job_complete = []

        # IDs of annotations to (re-)add to Elasticsearch because they're
        # either missing from Elasticsearch or are different in Elasticsearch
        # than in the DB.
        annotation_ids_to_sync = set()

        for job in jobs:
            annotation_id = URLSafeUUID.hex_to_url_safe(job.kwargs["annotation_id"])
            annotation_from_db = annotations_from_db.get(annotation_id)
            annotation_from_es = annotations_from_es.get(annotation_id)

            if job.kwargs.get("force", False):
                annotation_ids_to_sync.add(annotation_id)
                job_complete.append(job)
                counts[Result.SYNCED_FORCED.format(tag=job.tag)].add(annotation_id)
                counts[Result.SYNCED_TAG_TOTAL.format(tag=job.tag)].add(annotation_id)
                counts[Result.SYNCED_TOTAL].add(annotation_id)
                counts[Result.COMPLETED_FORCED.format(tag=job.tag)].add(job.id)
                counts[Result.COMPLETED_TAG_TOTAL.format(tag=job.tag)].add(job.id)
                counts[Result.COMPLETED_TOTAL].add(job.id)
            elif not annotation_from_db:
                job_complete.append(job)
                counts[Result.COMPLETED_DELETED.format(tag=job.tag)].add(job.id)
                counts[Result.COMPLETED_TAG_TOTAL.format(tag=job.tag)].add(job.id)
                counts[Result.COMPLETED_TOTAL].add(job.id)
            elif not annotation_from_es:
                annotation_ids_to_sync.add(annotation_id)
                counts[Result.SYNCED_MISSING.format(tag=job.tag)].add(annotation_id)
                counts[Result.SYNCED_TAG_TOTAL.format(tag=job.tag)].add(annotation_id)
                counts[Result.SYNCED_TOTAL].add(annotation_id)
            elif not self._equal(annotation_from_es, annotation_from_db):
                annotation_ids_to_sync.add(annotation_id)
                counts[Result.SYNCED_DIFFERENT.format(tag=job.tag)].add(annotation_id)
                counts[Result.SYNCED_TAG_TOTAL.format(tag=job.tag)].add(annotation_id)
                counts[Result.SYNCED_TOTAL].add(annotation_id)
            else:
                job_complete.append(job)
                counts[Result.COMPLETED_UP_TO_DATE.format(tag=job.tag)].add(job.id)
                counts[Result.COMPLETED_TAG_TOTAL.format(tag=job.tag)].add(job.id)
                counts[Result.COMPLETED_TOTAL].add(job.id)

        self._queue_service.delete(job_complete)

        if annotation_ids_to_sync:
            self._batch_indexer.index(list(annotation_ids_to_sync))

        return {key: len(value) for key, value in counts.items()}

    @staticmethod
    def _equal(annotation_from_es, annotation_from_db):
        """Test if the annotations are equal."""
        return (
            annotation_from_es["updated"] == annotation_from_db.updated
            and annotation_from_es["user"] == annotation_from_db.userid
        )

    def _get_annotations_from_db(self, annotation_ids):
        return {
            annotation.id: annotation
            for annotation in self._db.query(
                Annotation.id, Annotation.updated, Annotation.userid
            )
            .filter_by(deleted=False)
            .filter(Annotation.id.in_(annotation_ids))
        }

    def _get_annotations_from_es(self, annotation_ids):
        hits = self._es.conn.search(
            body={
                "_source": ["updated", "user"],
                "query": {"ids": {"values": list(annotation_ids)}},
                "size": len(annotation_ids),
            },
            index=self._es.index,
        )["hits"]["hits"]

        for hit in hits:
            updated = hit["_source"].get("updated")
            updated = isoparse(updated).replace(tzinfo=None) if updated else None
            hit["_source"]["updated"] = updated

        return {hit["_id"]: hit["_source"] for hit in hits}


def factory(_context, request):
    return AnnotationSyncService(
        batch_indexer=BatchIndexer(request.db, request.es, request),
        db=request.db,
        es=request.es,
        queue_service=request.find_service(name="queue_service"),
    )
