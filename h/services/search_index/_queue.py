import datetime
import logging

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

        # Jobs whose annotation is missing from or marked as deleted in the DB.
        missing_from_db = []

        # Jobs whose annotation is the same in Elasticsearch as in the DB.
        up_to_date_in_es = []

        # Annotation IDs that're in the DB but missing from Elasticsearch.
        missing_from_es = set()

        # IDs of annotations that are different in Elasticsearch than in the DB.
        different_in_es = set()

        for job in jobs:
            annotation_id = job.kwargs["annotation_id"]
            annotation_from_db = annotations_from_db.get(annotation_id)
            annotation_from_es = annotations_from_es.get(annotation_id)

            if not annotation_from_db:
                missing_from_db.append(job)
            elif not annotation_from_es:
                missing_from_es.add(job.kwargs["annotation_id"])
            elif annotation_from_es["updated"] != annotation_from_db.updated:
                different_in_es.add(job.kwargs["annotation_id"])
            else:
                up_to_date_in_es.append(job)

        if missing_from_db:
            logger.info(
                f"Deleting {len(missing_from_db)} sync annotation jobs because their annotations have been deleted from the DB"
            )
        if up_to_date_in_es:
            logger.info(
                f"Deleting {len(up_to_date_in_es)} successfully completed jobs from the queue"
            )

        for job in missing_from_db + up_to_date_in_es:
            self._db.delete(job)

        if missing_from_es:
            logger.info(
                f"Syncing {len(missing_from_es)} annotations that are missing from Elasticsearch"
            )

        if different_in_es:
            logger.info(
                f"Syncing {len(different_in_es)} annotations that are different in Elasticsearch"
            )

        if missing_from_es or different_in_es:
            self._batch_indexer.index(list(missing_from_es.union(different_in_es)))

    def _get_jobs_from_queue(self):
        return (
            self._db.query(Job)
            .filter(
                Job.scheduled_at < datetime.datetime.utcnow(),
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
