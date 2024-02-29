from collections import defaultdict

from dateutil.parser import isoparse

from h.db.types import URLSafeUUID
from h.models import Annotation, Job
from h.search.index import BatchIndexer


class AnnotationSyncService:
    """A service for synchronizing annotations from Postgres to Elasticsearch."""

    def __init__(self, batch_indexer, db_helper, es_helper, queue_service):
        self._batch_indexer = batch_indexer
        self._db_helper = db_helper
        self._es_helper = es_helper
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

        counter = Counter()
        annotations_from_db = self._db_helper.get(jobs)
        annotations_from_es = self._es_helper.get(jobs)

        for job in jobs:
            annotation_id = _url_safe_annotation_id(job)
            annotation_from_db = annotations_from_db.get(annotation_id)
            annotation_from_es = annotations_from_es.get(annotation_id)

            if job.kwargs.get("force", False):
                # If the job has force=True then always (re-)index the
                # annotation into Elasticsearch no matter what, even if the
                # annotation is already present and up-to-date in Elasticsearch.
                counter.annotation_synced(counter.Result.SYNCED_FORCED, job)
                counter.job_completed(counter.Result.COMPLETED_FORCED, job)
            elif (not annotation_from_db) and annotation_from_es:
                # The annotation isn't in the DB or is marked as
                # Annotation.deleted=True in the DB but it still present in
                # Elasticsearch. Delete the annotation from Elasticsearch.
                counter.annotation_deleted(counter.Result.SYNCED_DELETED, job)
            elif (not annotation_from_db) and (not annotation_from_es):
                # The annotation isn't in the DB or is marked as
                # Annotation.deleted=True in the DB and isn't in Elasticsearch
                # either. Delete the job from the queue, it has been completed.
                counter.job_completed(counter.Result.COMPLETED_DELETED, job)
            elif not annotation_from_es:
                # The annotation is present in the DB but missing from
                # Elasticsearch. Index the annotation into Elasticsearch.
                counter.annotation_synced(counter.Result.SYNCED_MISSING, job)
            elif not self._equal(annotation_from_es, annotation_from_db):
                # The annotation is present in Elasticsearch but different from
                # the copy in the DB. Re-index the annotation into Elasticsearch.
                counter.annotation_synced(counter.Result.SYNCED_DIFFERENT, job)
            else:
                # The annotation is present and up-to-date in Elasticsearch so
                # it doesn't need to be re-indexed. Delete the job from the
                # queue, it has been completed.
                counter.job_completed(counter.Result.COMPLETED_UP_TO_DATE, job)

        self._queue_service.delete(counter.jobs_to_delete)

        if counter.annotation_ids_to_sync:
            self._batch_indexer.index(counter.annotation_ids_to_sync)

        if counter.annotation_ids_to_delete:
            self._batch_indexer.delete(counter.annotation_ids_to_delete)

        return counter.counts

    @staticmethod
    def _equal(annotation_from_es, annotation_from_db):
        """Test if the annotations are equal."""
        return (
            annotation_from_es["updated"] == annotation_from_db.updated
            and annotation_from_es["user"] == annotation_from_db.userid
        )


class DBHelper:
    """Helper for woking with annotations in the DB."""

    def __init__(self, db):
        self._db = db

    def get(self, jobs: list[Job]) -> dict:
        """
        Return a dict of annotations from the DB for the given `jobs`.

        Return a dict mapping annotation IDs to their (annotation_id,
        annotation_updated_datetime, annotation_userid) tuples from the DB.

        If `jobs` contains multiple jobs for the same annotation these will be
        deduplicated and only one copy of the annotation will be returned.

        Any jobs with `Job.force=True` will be filtered out: their annotations
        won't be returned.

        Any annotations with `Annotation.deleted=True` in the DB will be
        filtered out and won't be returned.

        Any jobs whose annotations aren't in the DB will be filtered out:
        nothing will be returned for these jobs.
        """
        annotation_ids = _url_safe_annotation_ids(jobs)

        if not annotation_ids:
            return {}

        return {
            annotation.id: annotation
            for annotation in self._db.query(
                Annotation.id, Annotation.updated, Annotation.userid
            )
            .filter_by(deleted=False)
            .filter(Annotation.id.in_(annotation_ids))
        }


class ESHelper:
    """Helper for working with annotations in Elasticsearch."""

    def __init__(self, es):
        self._es = es

    def get(self, jobs: list[Job]) -> dict:
        """
        Return a dict of annotations from Elasticsearch for the given `jobs`.

        Return a dict mapping annotation IDs to their {"updated": <datetime>,
        "user": <userid>} dicts from Elasticsearch.

        If `jobs` contains multiple jobs for the same annotation this will be
        deduplicated and only one copy of the annotation will be returned.

        Any jobs with `Job.force=True` will be filtered out: their annotations
        won't be returned.

        Any jobs whose annotations aren't in the search index will be filtered
        out: nothing will be returned for these jobs.
        """
        annotation_ids = _url_safe_annotation_ids(jobs)

        if not annotation_ids:
            return {}

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
            if updated:
                updated = isoparse(updated).replace(tzinfo=None)
                hit["_source"]["updated"] = updated

        return {hit["_id"]: hit["_source"] for hit in hits if hit["_source"]}


class Counter:
    """A helper for counting metrics about work that AnnotationSyncService has done."""

    class Result:
        """String values for logging and metrics."""

        # These are in the style of New Relic custom metric names.
        SYNCED_MISSING = "Synced/{tag}/Missing_from_Elastic"
        SYNCED_DELETED = "Synced/{tag}/Deleted_from_db"
        SYNCED_DIFFERENT = "Synced/{tag}/Different_in_Elastic"
        SYNCED_FORCED = "Synced/{tag}/Forced"
        SYNCED_TAG_TOTAL = "Synced/{tag}/Total"
        SYNCED_TOTAL = "Synced/Total"
        COMPLETED_UP_TO_DATE = "Completed/{tag}/Up_to_date_in_Elastic"
        COMPLETED_DELETED = "Completed/{tag}/Deleted_from_db"
        COMPLETED_FORCED = "Completed/{tag}/Forced"
        COMPLETED_TAG_TOTAL = "Completed/{tag}/Total"
        COMPLETED_TOTAL = "Completed/Total"

    def __init__(self):
        self._counts = defaultdict(set)
        self._annotation_ids_to_sync = set()
        self._annotation_ids_to_delete = set()
        self._jobs_to_delete = set()

    def annotation_synced(self, metric, job: Job):
        """Record an annotation that will be (re-)synced to Elasticsearch."""
        annotation_id = _url_safe_annotation_id(job)

        self._annotation_ids_to_sync.add(annotation_id)
        self._counts[metric.format(tag=job.tag)].add(annotation_id)
        self._counts[self.Result.SYNCED_TAG_TOTAL.format(tag=job.tag)].add(
            annotation_id
        )
        self._counts[self.Result.SYNCED_TOTAL].add(annotation_id)

    def annotation_deleted(self, metric, job: Job):
        """Record an annotation that will be deleted from Elasticsearch."""
        annotation_id = _url_safe_annotation_id(job)

        self._annotation_ids_to_delete.add(annotation_id)
        self._counts[metric.format(tag=job.tag)].add(annotation_id)
        self._counts[self.Result.SYNCED_TAG_TOTAL.format(tag=job.tag)].add(
            annotation_id
        )
        self._counts[self.Result.SYNCED_TOTAL].add(annotation_id)

    def job_completed(self, metric, job: Job):
        """Record a job that will be completed."""
        self._jobs_to_delete.add(job)
        self._counts[metric.format(tag=job.tag)].add(job.id)
        self._counts[self.Result.COMPLETED_TAG_TOTAL.format(tag=job.tag)].add(job.id)
        self._counts[self.Result.COMPLETED_TOTAL].add(job.id)

    @property
    def annotation_ids_to_sync(self) -> list:
        """Return a list of the annotation IDs to be synced to Elasticsearch."""
        return list(self._annotation_ids_to_sync)

    @property
    def annotation_ids_to_delete(self) -> list:
        """Return a list of the annotation IDs to be deleted from Elasticsearch."""
        return list(self._annotation_ids_to_delete)

    @property
    def jobs_to_delete(self) -> list[Job]:
        """Return a list of the jobs to be deleted from the DB."""
        return list(self._jobs_to_delete)

    @property
    def counts(self) -> dict:
        """Return a dict of metrics of the work that has been done."""
        return {key: len(value) for key, value in self._counts.items()}


def _url_safe_annotation_ids(jobs):
    return {
        _url_safe_annotation_id(job)
        for job in jobs
        if not job.kwargs.get("force", False)
    }


def _url_safe_annotation_id(job):
    return URLSafeUUID.hex_to_url_safe(job.kwargs["annotation_id"])


def factory(_context, request):
    return AnnotationSyncService(
        batch_indexer=BatchIndexer(request.db, request.es, request),
        db_helper=DBHelper(db=request.db),
        es_helper=ESHelper(es=request.es),
        queue_service=request.find_service(name="queue_service"),
    )
