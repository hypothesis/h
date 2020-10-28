from collections import Counter
from datetime import datetime, timedelta
from logging import getLogger

from dateutil.parser import isoparse
from sqlalchemy import and_, func, select, text
from zope.sqlalchemy import mark_changed

from h.db.types import URLSafeUUID
from h.models import Annotation, Job

LOG = getLogger(__name__)


class Queue:
    """A job queue for synchronizing annotations from Postgres to Elastic."""

    class Priority:
        SINGLE_ITEM = 1
        SINGLE_USER = 100
        BETWEEN_TIMES = 1000

    class Result:
        # Values for reporting which should stringify nicely
        DELETED_FROM_DB = "Jobs deleted because annotations were deleted from the DB"
        MISSING = "Annotations synced because they were not in Elasticsearch"
        DIFFERENT = "Annotations synced because they were different in Elasticsearch"
        UP_TO_DATE = "Jobs deleted because annotations were up to date in Elasticsearch"
        FORCED = "Annotations synced because their jobs had force=True"

    def __init__(self, db, es, batch_indexer):
        self._db = db
        self._es = es
        self._batch_indexer = batch_indexer

    def add_where(self, where, tag, priority, force=False, schedule_in=None):
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
                    text("'sync_annotation'"),
                    text(f"'{schedule_at}'"),
                    text(str(priority)),
                    text(repr(tag)),
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
                counts[Queue.Result.FORCED] += 1
            elif not annotation_from_db:
                job_complete.append(job)
                counts[Queue.Result.DELETED_FROM_DB] += 1
            elif not annotation_from_es:
                annotation_ids_to_sync.add(annotation_id)
                counts[Queue.Result.MISSING] += 1
            elif not self._equal(annotation_from_es, annotation_from_db):
                annotation_ids_to_sync.add(annotation_id)
                counts[Queue.Result.DIFFERENT] += 1
            else:
                job_complete.append(job)
                counts[Queue.Result.UP_TO_DATE] += 1

        for job in job_complete:
            self._db.delete(job)

        if annotation_ids_to_sync:
            self._batch_indexer.index(list(annotation_ids_to_sync))

        LOG.info(dict(counts))

    def count(self, tags=None, expired=False):
        return self._job_query(tags=tags, expired=expired).count()

    def _get_jobs_from_queue(self, limit):
        return (
            self._job_query()
            .order_by(Job.priority, Job.enqueued_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
            .all()
        )

    def _job_query(self, tags=None, expired=False):
        now = datetime.utcnow()

        query = self._db.query(Job).filter(
            Job.name == "sync_annotation", Job.scheduled_at < now
        )

        if tags:
            query = query.filter(Job.tag.in_(tags))

        if expired:
            # Only find expired jobs.
            query = query.filter(Job.expires_at < now)
        else:
            # Only find jobs that aren't expired.
            query = query.filter(Job.expires_at >= now)

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
