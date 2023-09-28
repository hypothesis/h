from collections import defaultdict
from datetime import datetime, timedelta

from dateutil.parser import isoparse
from sqlalchemy import and_, func, literal_column, select
from zope.sqlalchemy import mark_changed

from h.db.types import URLSafeUUID
from h.models import Annotation, Job


class Queue:
    """A job queue for synchronizing annotations from Postgres to Elastic."""

    class Priority:
        SINGLE_ITEM = 1
        SINGLE_USER = 100
        SINGLE_GROUP = 100
        BETWEEN_TIMES = 1000

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

    def __init__(self, db, es, batch_indexer):
        self._db = db
        self._es = es
        self._batch_indexer = batch_indexer

    def add_where(  # pylint: disable=too-many-arguments
        self, where, tag, priority, force=False, schedule_in=None
    ):
        """
        Queue annotations matching a filter to be synced to ElasticSearch.

        :param where: A list of SQLAlchemy BinaryExpression objects to limit
            the annotations to be added
        :param tag: The tag to add to the job on the queue. For documentation
            purposes only
        :param priority: Integer priority value (higher number is lower
            priority)
        :param force: Whether to force reindexing of the annotation even if
            it's already indexed
        :param schedule_in: A number of seconds from now to wait before making
            the job available for processing. The annotation won't be synced
            until at least `schedule_in` seconds from now
        """
        where_clause = and_(*where) if len(where) > 1 else where[0]
        schedule_at = datetime.utcnow() + timedelta(seconds=schedule_in or 0)

        query = Job.__table__.insert().from_select(
            [Job.name, Job.scheduled_at, Job.priority, Job.tag, Job.kwargs],
            select(
                [
                    literal_column("'sync_annotation'"),
                    literal_column(f"'{schedule_at}'"),
                    literal_column(str(priority)),
                    literal_column(repr(tag)),
                    func.jsonb_build_object(
                        "annotation_id", Annotation.id, "force", bool(force)
                    ),
                ]
            ).where(where_clause),
        )

        self._db.execute(query)
        mark_changed(self._db)

    def add_between_times(self, start_time, end_time, tag, force=False):
        """
        Queue all annotations between two times to be synced to Elasticsearch.

        See Queue.add_where() for documentation of the params.

        :param start_time: The time to queue annotations from (inclusive)
        :param end_time: The time to queue annotations until (inclusive)
        """
        where = [Annotation.updated >= start_time, Annotation.updated <= end_time]
        self.add_where(where, tag, Queue.Priority.BETWEEN_TIMES, force)

    def add_by_id(self, annotation_id, tag, force=False, schedule_in=None):
        """
        Queue an annotation to be synced to Elasticsearch.

        See Queue.add_where() for documentation of the params.

        :param annotation_id: The ID of the annotation to be queued, in the
            application-level URL-safe format
        """
        where = [Annotation.id == annotation_id]
        self.add_where(where, tag, Queue.Priority.SINGLE_ITEM, force, schedule_in)

    def add_by_user(self, userid, tag, force=False, schedule_in=None):
        """
        Queue all a user's annotations to be synced to Elasticsearch.

        See Queue.add() for documentation of the params.

        :param userid: The ID of the user in "acct:USERNAME@AUTHORITY" format
        :type userid: unicode
        """
        where = [Annotation.userid == userid]
        self.add_where(where, tag, Queue.Priority.SINGLE_USER, force, schedule_in)

    def add_by_group(self, groupid, tag, force=False, schedule_in=None):
        """
        Queue all annotations in a group to be synced to Elasticsearch.

        See Queue.add() for documentation of the params.

        :param groupid: The pubid of the group
        :type groupid: unicode
        """
        where = [Annotation.groupid == groupid]
        self.add_where(where, tag, Queue.Priority.SINGLE_GROUP, force, schedule_in)

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
                counts[Queue.Result.SYNCED_FORCED.format(tag=job.tag)].add(
                    annotation_id
                )
                counts[Queue.Result.SYNCED_TAG_TOTAL.format(tag=job.tag)].add(
                    annotation_id
                )
                counts[Queue.Result.SYNCED_TOTAL].add(annotation_id)
                counts[Queue.Result.COMPLETED_FORCED.format(tag=job.tag)].add(job.id)
                counts[Queue.Result.COMPLETED_TAG_TOTAL.format(tag=job.tag)].add(job.id)
                counts[Queue.Result.COMPLETED_TOTAL].add(job.id)
            elif not annotation_from_db:
                job_complete.append(job)
                counts[Queue.Result.COMPLETED_DELETED.format(tag=job.tag)].add(job.id)
                counts[Queue.Result.COMPLETED_TAG_TOTAL.format(tag=job.tag)].add(job.id)
                counts[Queue.Result.COMPLETED_TOTAL].add(job.id)
            elif not annotation_from_es:
                annotation_ids_to_sync.add(annotation_id)
                counts[Queue.Result.SYNCED_MISSING.format(tag=job.tag)].add(
                    annotation_id
                )
                counts[Queue.Result.SYNCED_TAG_TOTAL.format(tag=job.tag)].add(
                    annotation_id
                )
                counts[Queue.Result.SYNCED_TOTAL].add(annotation_id)
            elif not self._equal(annotation_from_es, annotation_from_db):
                annotation_ids_to_sync.add(annotation_id)
                counts[Queue.Result.SYNCED_DIFFERENT.format(tag=job.tag)].add(
                    annotation_id
                )
                counts[Queue.Result.SYNCED_TAG_TOTAL.format(tag=job.tag)].add(
                    annotation_id
                )
                counts[Queue.Result.SYNCED_TOTAL].add(annotation_id)
            else:
                job_complete.append(job)
                counts[Queue.Result.COMPLETED_UP_TO_DATE.format(tag=job.tag)].add(
                    job.id
                )
                counts[Queue.Result.COMPLETED_TAG_TOTAL.format(tag=job.tag)].add(job.id)
                counts[Queue.Result.COMPLETED_TOTAL].add(job.id)

        for job in job_complete:
            self._db.delete(job)

        if annotation_ids_to_sync:
            self._batch_indexer.index(list(annotation_ids_to_sync))

        return {key: len(value) for key, value in counts.items()}

    def _get_jobs_from_queue(self, limit):
        return (
            self._job_query()
            .order_by(Job.priority, Job.enqueued_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
            .all()
        )

    def _job_query(self, tags=None, hide_scheduled=True):
        now = datetime.utcnow()

        query = self._db.query(Job).filter(
            Job.name == "sync_annotation", Job.expires_at >= now
        )

        if hide_scheduled:  # pragma: no cover
            query = query.filter(Job.scheduled_at < now)

        if tags:  # pragma: no cover
            query = query.filter(Job.tag.in_(tags))

        return query

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

    @staticmethod
    def _equal(annotation_from_es, annotation_from_db):
        """Test if the annotations are equal."""
        return (
            annotation_from_es["updated"] == annotation_from_db.updated
            and annotation_from_es["user"] == annotation_from_db.userid
        )
