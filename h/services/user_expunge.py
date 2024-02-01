import logging

from sqlalchemy import and_, delete, func, select, update

from h.models import (
    Annotation,
    AuthTicket,
    FeatureCohortUser,
    Flag,
    Group,
    GroupMembership,
    Job,
    Token,
    User,
)

log = logging.getLogger(__name__)


class UserExpungeService:
    def __init__(self, db, job_queue_svc, user_service, limit=10000):
        self.db = db
        self.job_queue_svc = job_queue_svc
        self.user_service = user_service
        self.limit = limit
        self.num_rows_deleted = 0

    def delete_user(self, userid):
        """
        Delete the given user.

        The user will be marked as deleted immediately. This will begin the
        process of expunging the user's data, in time all data belonging to
        this user will be deleted.
        """
        # Add a job to the job queue to delete the given user.
        self.db.add(
            Job(
                name="delete_user",
                priority=0,
                tag="h.tasks.enqueue_user_delete_job_to_queue",
                kwargs={"userid": userid},
            )
        )
        log.info("Enqueued 'delete_user' job")

    def expunge_deleted_users(self):
        """
        Incrementally expunge deleted users and their data.

        This task should be called periodically and will delete data belonging
        to any users who're marked as deleted. Each call will delete up to a
        fixed maximum amount of data. Calling this method repeatedly will
        eventually delete all data belonging to all deleted users.

        :arg max_rows_to_delete: the maximum number of rows to delete this call
        """
        try:
            job = self._get_user_delete_job()[0]
        except IndexError:
            # There are no user delete jobs on the queue.
            log.info("There are no 'user_delete' jobs")
            return

        userid = job.kwargs["userid"]

        user = self.user_service.fetch(userid)

        if user is None:
            log.info("Unknown userid: %s", userid)
            return

        log.info(f"Working on deleting user {userid}")

        # Delete data belonging to this user from various tables.
        #
        # We do this before deleting the user itself so that ON DELETE
        # CASCADE's don't cause the DB to try to delete too many rows in one
        # transaction.
        self.delete_authtickets(user)
        self.delete_flags(user)
        self.delete_featurecohort_memberships(user)
        self.delete_tokens(user)

        deleted_annotation_ids = self.delete_annotations(user)

        # Delete any groups that the user created and that no longer contain
        # any annotations. We do this *after* deleting the user's annotations:
        #
        # 1. So the user's own annotations don't stop groups from being deleted
        # 2. So we don't temporarily have annotations in the DB whose group no
        #    longer exists
        self.delete_groups(user)

        # Update any groups that the user created and that couldn't be deleted
        # because they still contain annotations from other users. We will
        # simply remove the user as the creator of these groups, leaving them
        # with no creator.
        self.delete_group_creators(user.id)

        # Remove the user's memberships of groups created by other users.
        self.delete_group_memberships(user)

        # Finally, delete the user itself.
        # We do this *after* deleting the user's annotations so we don't
        # temporarily have annotations in the DB whose user no longer exists.
        self.delete_rows(User, select(User.id).where(User.id == user.id))

        # Add jobs to the job table so that the deleted annotations also get
        # deleted from Elasticsearch. Importantly, this is done in the same
        # transaction in which the annotations were deleted from the DB.
        for row in deleted_annotation_ids:
            self.db.add(
                Job(
                    name="delete_annotation",
                    priority=0,
                    tag="h.services.user_expunge.expunge_deleted_users",
                    kwargs={"annotation_id": row.id},
                )
            )
            log.info("Enqueued 'delete_annotation' job")

        # Once we've deleted all data related to this user, finally remove the
        # job from the queue.
        if self.remaining_rows_to_delete:
            self.job_queue_svc.delete([job])
            log.info("Deleted job")

    def _get_user_delete_job(self):
        """Return a user delete job from the job queue."""
        return self.job_queue_svc.get("delete_user", 1)

    @property
    def remaining_rows_to_delete(self):
        return max(0, self.limit - self.num_rows_deleted)

    def delete_authtickets(self, user):
        return self.delete_rows(
            AuthTicket, select(AuthTicket.id).where(AuthTicket.user_id == user.id)
        )

    def delete_flags(self, user):
        return self.delete_rows(Flag, select(Flag.id).where(Flag.user_id == user.id))

    def delete_featurecohort_memberships(self, user):
        return self.delete_rows(
            FeatureCohortUser,
            select(FeatureCohortUser.id).where(FeatureCohortUser.user_id == user.id),
        )

    def delete_tokens(self, user):
        self.delete_rows(Token, select(Token.id).where(Token.userid == user.userid))

    def delete_annotations(self, user):
        return self.delete_rows(
            Annotation, select(Annotation.id).where(Annotation.userid == user.userid)
        )

    def delete_group_memberships(self, user):
        return self.delete_rows(
            GroupMembership,
            select(GroupMembership.id).where(GroupMembership.user_id == user.id),
        )

    def delete_groups(self, user):
        return self.delete_rows(
            Group,
            select(Group.id)
            .where(Group.creator_id == user.id)
            .outerjoin(
                Annotation,
                and_(
                    Annotation.groupid == Group.pubid,
                    Annotation.deleted.is_(False),
                ),
            )
            .group_by(Group.id)
            .having(func.count(Annotation.id) > 0),  # pylint:disable=not-callable
        )

    def delete_group_creators(self, user_id: int) -> int:
        """
        Remove `user_id` as the creator of up to `limit` groups.

        The groups will be left with no creator.

        :return: the number of groups that were modified
        """
        if not self.remaining_rows_to_delete:
            return

        self.num_rows_deleted += self.db.execute(
            update(Group)
            .where(
                Group.id.in_(
                    select(
                        select(Group.id)
                        .where(Group.creator_id == user_id)
                        .limit(self.remaining_rows_to_delete)
                        .cte()
                    )
                )
            )
            .values(creator_id=None)
        ).rowcount

    def delete_rows(self, model_class, select_stmnt):
        if not self.remaining_rows_to_delete:
            return []

        deleted_ids = self.db.execute(
            delete(model_class)
            .where(
                model_class.id.in_(
                    select(select_stmnt.limit(self.remaining_rows_to_delete).cte())
                )
            )
            .returning(model_class.id)
        ).all()

        num_rows_deleted = len(deleted_ids)
        self.num_rows_deleted += num_rows_deleted
        log.info("Deleted %d rows from %s", num_rows_deleted, model_class)

        return deleted_ids


def factory(_context, request):
    return UserExpungeService(
        db=request.db,
        job_queue_svc=request.find_service(name="queue_service"),
        user_service=request.find_service(name="user"),
    )
