import datetime
import logging

from dateutil.parser import isoparse

from h.models import Annotation, Job
from h.search.index import BatchIndexer

logger = logging.getLogger(__name__)


class JobQueue:
    """
    A simple transactional job queue that consumes jobs from a DB table.

    This home-grown job queue differs from our Celery task queue in a few ways:

    1. The job queue is stored in Postgres so jobs can be added as part of a
       Postgres transaction.

       For example a new annotation can be added to the annotations table
       and a job to synchronize that annotation into Elasticsearch can be added
       to the job queue as part of the same Postgres transaction. This way it's
       not possible to add an annotation to Postgres and fail to add it to the
       job queue or vice-versa. The two can't get out of sync because they're
       part of a single Postgres transaction.

    2. The job queue is less immediate.

       Jobs are processed in batch by a periodic Celery task that runs every N
       minutes (see h-periodic for how frequently the task is run) so a job
       added to the job queue might not get processed until N minutes later (or
       even longer: if the job queue is currently long then the periodic task
       may have to run multiple times before it gets to your job).

       In contrast tasks added to Celery can be processed by a worker almost
       immediately.

    3. The job queue is very simple and has far fewer features than Celery.

    Celery should be the default task queue for almost all tasks, and only jobs
    that really need Postgres transactionality should use this custom job
    queue.

    At the time of writing this job queue only supports a single type of job:
    synchronizing annotations from Postgres to Elasticsearch.
    """

    def __init__(self, db, es, batch_indexer, limit):
        self._db = db
        self._es = es
        self._batch_indexer = batch_indexer
        self._limit = limit

    def add_sync_annotation_job(self, annotation_id, tag, scheduled_at=None):
        """Add an annotation to be synced to Elasticsearch."""
        self.add_sync_annotation_jobs([annotation_id], tag, scheduled_at)

    def add_sync_annotation_jobs(self, annotation_ids, tag, scheduled_at=None):
        """Add a list of annotations to the queue to be synced to Elasticsearch."""
        self._db.add_all(
            Job(
                tag=tag,
                scheduled_at=scheduled_at,
                kwargs={"annotation_id": annotation_id},
            )
            for annotation_id in annotation_ids
        )

    def sync_annotations(self):
        """
        Synchronize annotations from Postgres to Elasticsearch.

        This method is meant to be run periodically. It's called by a Celery
        task that's scheduled periodically by h-periodic.

        Each time this method runs it considers a fixed number of sync
        annotation jobs from the job queue. For each job, if the annotation is
        already present and up to date in Elasticsearch, then it removes the
        job from the queue. If the annotation is missing from Elasticsearch or
        out of date in Elasticsearch then the method re-syncs the annotation
        into Elasticsearch, and leaves the job on the queue to be re-checked
        and removed the next time the method runs.

        If the DB somehow contains an annotation that always fails to index
        into Elasticsearch, then a job for that annotation will never be
        removed from the queue! As far as I know it isn't possible for the DB
        to contain such an annotation.
        """
        jobs = self._get_jobs_from_queue()

        if not jobs:
            return

        annotation_ids = [job.kwargs["annotation_id"] for job in jobs]
        annotations_from_db = self._get_annotations_from_db(annotation_ids)
        annotations_from_es = self._get_annotations_from_es(annotation_ids)

        missing_from_db = []
        missing_from_es = []
        different_in_es = []
        up_to_date_in_es = []

        for job in jobs:
            annotation_id = job.kwargs["annotation_id"]
            annotation_from_db = annotations_from_db.get(annotation_id)
            annotation_from_es = annotations_from_es.get(annotation_id)

            if not annotation_from_db:
                missing_from_db.append(job)
            elif not annotation_from_es:
                missing_from_es.append(job)
            elif annotation_from_es["updated"] != annotation_from_db.updated:
                different_in_es.append(job)
            else:
                up_to_date_in_es.append(job)

        if missing_from_db:
            logger.info(
                f"Deleting {len(missing_from_db)} sync annotation jobs because their annotations have been deleted from the DB"
            )
        if up_to_date_in_es:
            logger.info(
                f"Deleting {len(up_to_date_in_es)} successfully synced annotations from job queue"
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
            self._batch_indexer.index(
                [
                    job.kwargs["annotation_id"]
                    for job in missing_from_es + different_in_es
                ]
            )

    def _get_jobs_from_queue(self):
        return (
            self._db.query(Job)
            .filter(
                Job.scheduled_at < datetime.datetime.utcnow(),
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
                "query": {"ids": {"values": annotation_ids}},
                "size": len(annotation_ids),
            }
        )["hits"]["hits"]

        for hit in hits:
            updated = hit["_source"].get("updated")
            updated = isoparse(updated).replace(tzinfo=None) if updated else None
            hit["_source"]["updated"] = updated

        return {hit["_id"]: hit["_source"] for hit in hits}


def factory(context, request):
    return JobQueue(
        db=request.db,
        es=request.es,
        batch_indexer=BatchIndexer(request.db, request.es, request),
        limit=request.registry.settings["h.es_sync_job_limit"],
    )
