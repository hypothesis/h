import logging
from datetime import datetime

from sqlalchemy import and_, delete, func, select, update

from h.models import (
    Annotation,
    AnnotationSlim,
    AuthTicket,
    FeatureCohortUser,
    Flag,
    Group,
    GroupMembership,
    Job,
    Token,
    User,
    UserDeletion,
)

log = logging.getLogger(__name__)


class UserDeleteService:

    def __init__(self, db, job_queue, user_svc):
        self.db = db
        self.job_queue = job_queue
        self.user_svc = user_svc

    def delete_user(self, user: User, requested_by: User, tag: str):
        """Mark `user` as deleted and start purging their data in the background."""

        # Mark the user as deleted so they can't login anymore.
        user.deleted = True

        # We can't just purge all the user's data right now because for users
        # with a lot of data this takes too long for an HTTP request and the
        # request times out.
        #
        # So add a job to purge the user's data in the background.
        self.db.add(
            Job(
                name=Job.JobName.PURGE_USER,
                priority=0,
                tag="UserDeleteService.delete_user",
                kwargs={"userid": user.userid},
            )
        )

        # Record the deletion for record-keeping purposes.
        self.db.add(
            UserDeletion(
                userid=user.userid,
                requested_by=requested_by.userid,
                tag=tag,
                registered_date=user.registered_date,
                num_annotations=self.db.scalar(
                    select(
                        func.count(Annotation.id)  # pylint:disable=not-callable
                    ).where(Annotation.userid == user.userid)
                ),
            )
        )

    def purge_deleted_users(self, limit=1000):
        """Incrementally purge data of users who've been marked as deleted."""
        jobs = self.job_queue.get(Job.JobName.PURGE_USER, limit)

        if not jobs:
            return

        completed_jobs = []
        purger = UserPurger(self.db, self.job_queue, LimitedWorker(self.db, limit))

        for job in jobs:
            userid = job.kwargs.get("userid")

            if not userid:
                log.info("Invalid '%s' job: %s", job.JobName.PURGE_USER, job)
                completed_jobs.append(job)
                continue

            user = self.user_svc.fetch(userid)

            if user is None:
                log.info("Couldn't fetch user: %s", userid)
                completed_jobs.append(job)
                continue

            log.info("Purging user: %s", user.userid)

            try:
                purger.delete_authtickets(user)
                purger.delete_tokens(user)
                purger.delete_flags(user)
                purger.delete_featurecohort_memberships(user)
                purger.delete_annotations(user)
                purger.delete_groups(user)
                purger.delete_group_memberships(user)
                purger.delete_group_creators(user)
                purger.delete_user(user)
            except LimitReached:
                break
            else:
                completed_jobs.append(job)

        self.job_queue.delete(completed_jobs)


class UserPurger:
    """Helper methods for purging data belonging to a given user."""

    def __init__(self, db, job_queue, worker):
        self.db = db
        self.job_queue = job_queue
        self.worker = worker

    def delete_authtickets(self, user):
        """Delete all AuthTicket's belonging to `user`."""
        self.worker.delete(
            AuthTicket, select(AuthTicket.id).where(AuthTicket.user == user)
        )

    def delete_tokens(self, user):
        """Delete all tokens belonging to `user`."""
        self.worker.delete(Token, select(Token.id).where(Token.user == user))

    def delete_flags(self, user):
        """Delete all flags created by `user`."""
        self.worker.delete(Flag, select(Flag.id).where(Flag.user_id == user.id))

    def delete_featurecohort_memberships(self, user):
        """Remove `user` from all feature cohorts."""
        self.worker.delete(
            FeatureCohortUser,
            select(FeatureCohortUser.id).where(FeatureCohortUser.user_id == user.id),
        )

    def delete_annotations(self, user):
        """Delete all of `user`'s annotations from both Postgres and Elasticsearch."""
        now = datetime.utcnow()

        deleted_annotation_ids = self.worker.update(
            Annotation,
            select(Annotation.id)
            .where(Annotation.userid == user.userid)
            .where(Annotation.deleted.is_(False)),
            {
                # We don't actually delete the user's annotations from the DB,
                # we only mark them as deleted.
                # The marked-as-deleted annotations will later be purged by the
                # periodic purge_deleted_annotations() task.
                #
                # This is because there are parts of h that don't work if
                # annotations are deleted immediately, including the WebSocket
                # and the call to JobQueueService.add_by_id() below.
                #
                # This is the same as what happens when annotations are deleted
                # individually by the API.
                "deleted": True,
                # Bump the annotation's updated time when marking it as deleted.
                # This is to prevent the purge_deleted_annotations() task from
                # purging the annotation too soon: that task only purges
                # deleted annotations whose updated time is more than ten mins
                # ago.
                "updated": now,
            },
        )

        # Whenever we update annotations we also need to update the corresponding annotation_slims.
        num_deleted_annotation_slims = self.db.execute(
            update(AnnotationSlim)
            .where(AnnotationSlim.pubid.in_(deleted_annotation_ids))
            .values({"deleted": True, "updated": now})
        ).rowcount
        if num_deleted_annotation_slims:
            log.info(
                "Updated %d rows from annotation_slim", num_deleted_annotation_slims
            )
        else:  # pragma: nocover
            pass

        # Add jobs to the queue so the annotations will eventually be deleted from Elasticsearch.
        for annotation_id in deleted_annotation_ids:
            self.job_queue.add_by_id(
                name="sync_annotation",
                annotation_id=annotation_id,
                tag="UserDeleteService.delete_annotations",
                schedule_in=60,
            )
        log.info(
            "Enqueued jobs to delete %i annotations from Elasticsearch",
            len(deleted_annotation_ids),
        )

    def delete_groups(self, user):
        """
        Delete groups owned by `user` that have no annotations.

        Delete groups that that `user` is the *only* owner of and that don't
        contain any non-deleted annotations.

        If delete_annotations() (above) is called first then all of `user`'s
        own annotations will already have been deleted, so ultimately any
        groups that `user` is the only owner of and that don't contain any
        annotations by *other* users will get deleted.

        Known issue: if this method does not delete a group because it contains
        annotations by other users, and those annotations other users are later
        deleted, then the group will no longer contain any annotations but will
        never be deleted.

        Known issue: this will also delete all of the groups memberships due to
        a foreign key constraint with ondelete="cascade". If a group had a
        really large number of members this could take too long and cause a
        timeout.
        """
        # pylint:disable=not-callable
        # pylint:disable=use-implicit-booleaness-not-comparison-to-zero

        # The IDs of all groups that have only one owner.
        groups_with_only_one_owner = (
            select(GroupMembership.group_id)
            .where(GroupMembership.roles.contains(["owner"]))
            .group_by(GroupMembership.group_id)
            .having(func.count(GroupMembership.group_id) == 1)
        )

        # The IDs of all groups where `user` is the only owner.
        groups_where_user_is_only_owner = (
            select(GroupMembership.group_id)
            .where(GroupMembership.group_id.in_(groups_with_only_one_owner))
            .where(GroupMembership.roles.contains(["owner"]))
            .where(GroupMembership.user_id == user.id)
        )

        # The IDs of all groups where `user` is the only owner *and* the group
        # doesn't contain any annotations by other users.
        groups_to_be_deleted = (
            select(Group.id)
            .where(Group.id.in_(groups_where_user_is_only_owner))
            .outerjoin(
                Annotation,
                and_(Annotation.groupid == Group.pubid, Annotation.deleted.is_(False)),
            )
            .group_by(Group.id)
            .having(func.count(Annotation.id) == 0)
        )

        self.worker.delete(Group, groups_to_be_deleted)

    def delete_group_memberships(self, user):
        """
        Delete `user`'s group memberships.

        Known issue: this can leave groups that were created by `user` in an
        odd state - `user` will no longer be a member of the group but will
        still be its creator. But this state can occur in other ways as well,
        for example the web interface currently allows a group's creator to
        leave the group.

        If `delete_group_creators()` (below) is called after this method then
        the situation will be only temporary: `user` will soon be removed as
        the group's creator as well.
        """
        self.worker.delete(
            GroupMembership,
            select(GroupMembership.id)
            .where(GroupMembership.user_id == user.id)
            .join(Group, GroupMembership.group_id == Group.id),
        )

    def delete_group_creators(self, user):
        """
        Delete `user` as the creator of any groups they created.

        Known issue: this will leave groups in an odd state - with no creator
        (group.creator = None).
        """
        self.worker.update(
            Group, select(Group.id).where(Group.creator == user), {"creator_id": None}
        )

    def delete_user(self, user):
        """Delete `user`."""
        self.worker.delete(User, select(User.id).where(User.id == user.id))


class LimitReached(Exception):
    """A LimitedWorker has reached its limit and won't do any more work."""


class LimitedWorker:
    """
    Executes given SQL statements until it has affected `limit` rows.

    Once a LimitedWorker instance has updated or deleted `limit` rows (across
    all SQL statements that it has executed) it refuses to do any more work: if
    you ask it to execute any more statments it'll raise `LimitReached`.

    For example:

        >>> worker = LimitedWorker(db, limit=10)

        >>> # Update 6 rows. Reduces `worker.limit` from 10 to 4.
        >>> worker.update(ModelClass, select_stmnt_matching_6_rows, values)

        >>> # Update 2 more rows. Reduces `worker.limit` from 4 to 2.
        >>> worker.update(ModelClass, select_stmnt_matching_2_rows, values)

        >>> # Even though the given delete statement matches 4 rows this will
        >>> # only delete 2 rows because `worker.limit` is only 2.
        >>> # This will reduce `worker.limit` from 2 to 0.
        >>> worker.delete(ModelClass, select_stmnt_matching_4_rows, values)

        >>> # Now that `worker.limit` is 0 any further calls will raise LimitReached.
        >>> worker.update(...)
        LimitReached()

        >>> worker.delete(...)
        LimitReached()

    """

    def __init__(self, db, limit: int):
        self.db = db
        self.limit = limit

    def update(self, model_class, select_stmnt, values: dict) -> list:
        """
        Update up to self.limit rows matching select_stmnt with `values`.

        :return: the IDs of the rows that were updated
        """
        updated_ids = self._execute(
            update(model_class)
            .where(model_class.id.in_(select(select_stmnt.limit(self.limit).cte())))
            .values(values)
            .returning(model_class.id)
        )
        if updated_ids:
            log.info(
                "Updated %d rows from %s", len(updated_ids), model_class.__tablename__
            )
        return updated_ids

    def delete(self, model_class, select_stmnt) -> list:
        """
        Delete up to self.limit rows matching select_stmnt.

        :return: the IDs of the rows that were deleted
        """
        deleted_ids = self._execute(
            delete(model_class)
            .where(model_class.id.in_(select(select_stmnt.limit(self.limit).cte())))
            .returning(model_class.id)
        )
        if deleted_ids:
            log.info(
                "Deleted %d rows from %s", len(deleted_ids), model_class.__tablename__
            )
        return deleted_ids

    def _execute(self, stmnt):
        if self.limit < 1:
            raise LimitReached()

        affected_ids = self.db.scalars(stmnt).all()
        self.limit -= len(affected_ids)

        return affected_ids


def service_factory(_context, request):
    return UserDeleteService(
        request.db,
        job_queue=request.find_service(name="queue_service"),
        user_svc=request.find_service(name="user"),
    )
