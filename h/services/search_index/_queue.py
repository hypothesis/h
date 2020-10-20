import logging
from collections import Counter
from datetime import datetime

from dateutil.parser import isoparse
from sqlalchemy import func, select, text
from zope.sqlalchemy import mark_changed

from h.db.types import URLSafeUUID
from h.models import Annotation, Job

logger = logging.getLogger(__name__)

# Strings used in log messages.
DELETED_FROM_DB = "Jobs deleted because annotations were deleted from the DB"
MISSING = "Annotations synced because they were not in Elasticsearch"
OUT_OF_DATE = "Annotations synced because they were outdated in Elasticsearch"
UP_TO_DATE = "Jobs deleted because annotations were up to date in Elasticsearch"
FORCED = "Annotations synced because their jobs had force=True"


class Queue:
    """A job queue for synchronizing annotations from Postgres to Elastic."""

    def __init__(self, db, es, batch_indexer):
        self._db = db
        self._es = es
        self._batch_indexer = batch_indexer

    def add(self, annotation_id, tag, schedule_in=None, force=False):
        """Queue an annotation to be synced to Elasticsearch."""
        self.add_all([annotation_id], tag, schedule_in, force)

    def add_all(self, annotation_ids, tag, schedule_in=None, force=False):
        """Queue a list of annotations to be synced to Elasticsearch."""

        scheduled_at = (datetime.utcnow() + schedule_in) if schedule_in else None

        # Jobs with a lower number for their priority get processed before jobs
        # with a higher number. Make large batches of jobs added all at once
        # get processed *after* small batches added a few at a time, so that
        # large batches don't hold up small ones for a long time.
        priority = len(annotation_ids)

        self._db.add_all(
            Job(
                tag=tag,
                name="sync_annotation",
                scheduled_at=scheduled_at,
                priority=priority,
                kwargs={
                    "annotation_id": URLSafeUUID.url_safe_to_hex(annotation_id),
                    "force": force,
                },
            )
            for annotation_id in annotation_ids
        )

    def add_annotations_between_times(self, start_time, end_time, tag, force=False):
        self._db.execute(
            Job.__table__.insert().from_select(
                [Job.name, Job.priority, Job.tag, Job.kwargs],
                select(
                    [
                        text("'sync_annotation'"),
                        text("1000"),
                        text(repr(tag)),
                        func.jsonb_build_object(
                            "annotation_id", Annotation.id, "force", force
                        ),
                    ]
                )
                .where(Annotation.updated >= start_time)
                .where(Annotation.updated <= end_time),
            )
        )
        mark_changed(self._db)

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
        jobs = self._get_jobs_from_queue(limit)

        if not jobs:
            return

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

        counts = Counter()

        for job in jobs:
            annotation_id = URLSafeUUID.hex_to_url_safe(job.kwargs["annotation_id"])
            annotation_from_db = annotations_from_db.get(annotation_id)
            annotation_from_es = annotations_from_es.get(annotation_id)

            if job.kwargs.get("force", False):
                annotation_ids_to_sync.add(annotation_id)
                job_complete.append(job)
                counts[FORCED] += 1
            elif not annotation_from_db:
                job_complete.append(job)
                counts[DELETED_FROM_DB] += 1
            elif not annotation_from_es:
                annotation_ids_to_sync.add(annotation_id)
                counts[MISSING] += 1
            elif annotation_from_es["updated"] != annotation_from_db.updated:
                annotation_ids_to_sync.add(annotation_id)
                counts[OUT_OF_DATE] += 1
            else:
                job_complete.append(job)
                counts[UP_TO_DATE] += 1

        for job in job_complete:
            self._db.delete(job)

        if annotation_ids_to_sync:
            self._batch_indexer.index(list(annotation_ids_to_sync))

        logger.info(dict(counts))

    def _get_jobs_from_queue(self, limit):
        return (
            self._db.query(Job)
            .filter(
                Job.name == "sync_annotation",
                Job.scheduled_at < datetime.utcnow(),
            )
            .order_by(Job.priority, Job.enqueued_at)
            .limit(limit)
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
            },
            index=self._es.index,
        )["hits"]["hits"]

        for hit in hits:
            updated = hit["_source"].get("updated")
            updated = isoparse(updated).replace(tzinfo=None) if updated else None
            hit["_source"]["updated"] = updated

        return {hit["_id"]: hit["_source"] for hit in hits}
