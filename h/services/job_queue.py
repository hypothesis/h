from datetime import datetime, timedelta

from sqlalchemy import and_, func, literal_column, select
from zope.sqlalchemy import mark_changed

from h.models import Annotation, Job


class Priority:
    SINGLE_ITEM = 1
    SINGLE_USER = 100
    SINGLE_GROUP = 100
    BETWEEN_TIMES = 1000


class JobQueueService:
    def __init__(self, db):
        self._db = db

    def get(self, name, limit):
        now = datetime.utcnow()

        query = self._db.query(Job).filter(
            Job.name == name, Job.expires_at >= now, Job.scheduled_at < now
        )

        return (
            query.order_by(Job.priority, Job.enqueued_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
            .all()
        )

    def delete(self, jobs):
        for job in jobs:
            self._db.delete(job)

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def add_between_times(self, name, start_time, end_time, tag, force=False):
        """
        Queue all annotations between two times.

        See Queue.add_where() for documentation of the params.

        :param start_time: The time to queue annotations from (inclusive)
        :param end_time: The time to queue annotations until (inclusive)
        """
        where = [Annotation.updated >= start_time, Annotation.updated <= end_time]
        self.add_where(name, where, tag, Priority.BETWEEN_TIMES, force)

    def add_by_id(self, name, annotation_id, tag, force=False, schedule_in=None):
        """
        Queue an annotation.

        See Queue.add_where() for documentation of the params.

        :param annotation_id: The ID of the annotation to be queued, in the
            application-level URL-safe format
        """
        where = [Annotation.id == annotation_id]
        self.add_where(name, where, tag, Priority.SINGLE_ITEM, force, schedule_in)

    def add_by_user(self, name, userid: str, tag, force=False, schedule_in=None):
        """
        Queue all a user's annotations.

        See Queue.add() for documentation of the params.

        :param userid: The ID of the user in "acct:USERNAME@AUTHORITY" format
        """
        where = [Annotation.userid == userid]
        self.add_where(name, where, tag, Priority.SINGLE_USER, force, schedule_in)

    def add_by_group(self, name, groupid: str, tag, force=False, schedule_in=None):
        """
        Queue all annotations in a group.

        See Queue.add() for documentation of the params.

        :param groupid: The pubid of the group
        """
        where = [Annotation.groupid == groupid]
        self.add_where(name, where, tag, Priority.SINGLE_GROUP, force, schedule_in)

    def add_where(
        self,
        name,
        where,
        tag,
        priority,
        force=False,
        schedule_in=None,
    ):
        """
        Queue annotations matching a filter .

        :param name : Name of the task in the queue
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
                literal_column(f"'{name}'"),
                literal_column(f"'{schedule_at}'"),
                literal_column(str(priority)),
                literal_column(repr(tag)),
                func.jsonb_build_object(
                    "annotation_id", Annotation.id, "force", bool(force)
                ),
            ).where(where_clause),
        )

        self._db.execute(query)
        mark_changed(self._db)


def factory(_context, request):
    return JobQueueService(request.db)
