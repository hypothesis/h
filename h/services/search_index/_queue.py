import logging
from collections import defaultdict
from datetime import datetime

from dateutil.parser import isoparse

from h.models import Annotation, Job

logger = logging.getLogger(__name__)


class Queue:
    """A job queue for synchronizing annotations from Postgres to Elastic."""

    def __init__(self, db, es, batch_indexer, limit):
        self._db = db
        self._es = es
        self._batch_indexer = batch_indexer
        self._limit = limit

    def add(self, annotation_id, tag, scheduled_at=None):
        """Queue an annotation to be synced to Elasticsearch."""
        self.add_all([annotation_id], tag, scheduled_at)

    def add_all(self, annotation_ids, tag, scheduled_at=None):
        """Queue a list of annotations to be synced to Elasticsearch."""

        if scheduled_at is not None:
            scheduled_at = datetime.utcnow() + scheduled_at

        self._db.add_all(
            Job(
                tag=tag,
                name="sync_annotation",
                scheduled_at=scheduled_at,
                kwargs={"annotation_id": annotation_id},
            )
            for annotation_id in annotation_ids
        )

    def sync(self):
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
        jobs = self._get_jobs_from_queue()

        if not jobs:
            return

        annotation_ids = {job.kwargs["annotation_id"] for job in jobs}
        annotations_from_db = self._get_annotations_from_db(annotation_ids)
        annotations_from_es = self._get_annotations_from_es(annotation_ids)

        job_complete = []
        annotations_to_sync = set()
        counts = defaultdict(lambda: 0)

        for job in jobs:
            annotation_id = job.kwargs["annotation_id"]
            annotation_from_db = annotations_from_db.get(annotation_id)
            annotation_from_es = annotations_from_es.get(annotation_id)

            if not annotation_from_db:
                job_complete.append(job)
                counts['missing_from_db'] += 1
            if not annotation_from_es:
                annotations_to_sync.add(annotation_id)
                counts['missing_from_es'] += 1
            elif annotation_from_es["updated"] != annotation_from_db.updated:
                annotations_to_sync.add(annotation_id)
                counts['different_in_es'] += 1
            else:
                job_complete.append(job)
                counts['up_to_date_in_es'] += 1

        for job in job_complete:
            counts['deleted_job'] += 1
            self._db.delete(job)

        if annotations_to_sync:
            counts['indexed'] = len(annotations_to_sync)
            self._batch_indexer.index(list(annotations_to_sync))

        logger.info(f"Job sync complete: {counts}")
        return counts

    def _get_jobs_from_queue(self):
        return (
            self._db.query(Job)
            .filter(
                Job.scheduled_at < datetime.utcnow(),
                Job.name == "sync_annotation",
            )
            .order_by(Job.enqueued_at)
            .limit(self._limit)
            .with_for_update(skip_locked=True)
            .all()
        )

    def _get_annotations_from_db(self, annotation_ids):
        return {
            annotation.id: annotation
            for annotation in self._db.query(Annotation.id, Annotation.updated)
            .filter_by(deleted=False)
            .filter(Annotation.id.in_(annotation_ids))
        }

    def _get_annotations_from_es(self, annotation_ids):
        hits = self._es.conn.search(
            body={
                "_source": ["updated"],
                "query": {"ids": {"values": list(annotation_ids)}},
                "size": len(annotation_ids),
            }
        )["hits"]["hits"]

        for hit in hits:
            updated = hit["_source"].get("updated")
            updated = isoparse(updated).replace(tzinfo=None) if updated else None
            hit["_source"]["updated"] = updated

        return {hit["_id"]: hit["_source"] for hit in hits}
