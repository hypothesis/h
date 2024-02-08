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


class UserDeleteService:
    def __init__(self, db, job_queue_svc, user_svc, limit=1):
        self.db = db
        self.job_queue_svc = job_queue_svc
        self.user_svc = user_svc
        self.limit = limit
        self.num_rows_deleted = 0
        print("I am UserDeleteService")

    def delete_user(self, user):
        """
        Delete the given user.

        The user will be marked as deleted and their account disabled
        immediately.  All the user's data will then be deleted in time by a
        background task.
        """
        # Trying to delete the user before we've deleted all their data could:
        #
        # - Crash, if there are rows in other tables with foreign key constraints
        #   without ON DELETE CASCADE
        # - Try to do too much work in a single query, if there are rows in
        #   other tables with foreign key constraints *with* ON DELETE CASCADE
        # - Leaves data in an inconsistent state, if there are rows in other
        #   tables that refer to this user but without a foreign key constraint
        #
        # So we don't want to actually delete the user just yet. But we'll mark
        # them as deleted immediately so they can't log in anymore.
        user.deleted = True

        # TODO: We should scramble certain fields of the user row immediately,
        # rather than waiting for it to be deleted by a background task.
        # For example rows that contain sensitive data like the email address
        # and password.

        # Add a job to delete the user. This will ensure that in time all the
        # user's data will be deleted by a background task.
        self.db.add(
            Job(
                name="delete_user",
                priority=0,
                tag="h.tasks.enqueue_user_delete_job_to_queue",
                kwargs={"userid": user.userid},
            )
        )

        # Most of the user's data will be deleted over time by a background
        # task that processes the job we just added to the queue. But there are
        # certain things that we should delete now in order to immediately
        # disable the account.
        self.db.execute(delete(AuthTicket).where(AuthTicket.user_id == user.id))
        self.db.execute(delete(Token).where(Token.userid == user.userid))

    def expunge_deleted_users(self):
        """
        Incrementally delete data belonging to users who've been marked as deleted.

        This task should be called periodically and will delete data belonging
        to any users who're marked as deleted. Each call will delete up to a
        fixed maximum number of rows from the DB. Calling this method
        repeatedly will eventually delete all data belonging to all deleted
        users.
        """
        try:
            job = self.job_queue_svc.get("delete_user", 1)[0]
        except IndexError:
            log.info("There are no 'delete_user' jobs to do")
            return

        user = self.user_svc.fetch(job.kwargs["userid"])

        if user is None:
            log.info("Couldn't fetch user: %s", job.kwargs["userid"])
            return

        log.info("Working on deleting user %s", user.userid)

        # Delete data belonging to this user from various tables.
        #
        # These are tables that're related to the `user` table (or to some
        # other table we're going to delete rows from later) and that:
        #
        # * Have foreign key constraints *without* ON DELETE CASCADE:
        #   attempting to delete the `user` row will crash if the rows from
        #   these tables aren't deleted first.
        # * Have foreign key constraints *with* ON DELETE CASCADE:
        #   attempting to delete the `user` row could take too long if it
        #   causes the DB to try to cascade-delete a lot of related rows.
        # * Don't have foreign key constraints at all:
        #   we have to delete these rows manually or they'll be left behind.
        #   We should delete these *before* deleting the user itself so that we
        #   don't temporarily have rows in other tables referencing a user that
        #   no longer exists.
        self.delete_flags(user)
        self.delete_featurecohort_memberships(user)

        # Delete the user's annotations.
        # Do this before deleting the user itself so we don't temporarily have
        # annotations whose userid no longer exists in the `user` table.
        deleted_annotation_ids = self.delete_annotations(user)

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
            log.info("Enqueued job to delete annotation %s", row.id)

        # Delete any groups that the user created and that no longer contain
        # any annotations. Do this *after* deleting the user's annotations so
        # that:
        #
        # 1. The user's own annotations don't stop groups from being deleted
        # 2. We don't temporarily have annotations in the DB whose group no
        #    longer exists
        self.delete_groups(user)

        # Update any groups that the user created and that couldn't be deleted
        # because they still contain annotations from other users. We will
        # simply remove the user as the creator of these groups, leaving them
        # with no creator.
        self.delete_group_creators(user)

        # Remove the user's memberships of groups created by other users.
        self.delete_group_memberships(user)

        # Delete the user itself.
        # FIXME: Once we delete the actual `user` row this username and email address
        # can be reused to register a new account.
        # So don't actually delete the user here. Instead, add a delete_user
        # job to the job queue and schedule it to run in 48hrs time or maybe in
        # a week's time. This is to allow time for data related to this user to
        # clear itself from the search index, message queue, and caches.
        self.delete_rows(User, select(User.id).where(User.id == user.id))

        # Once we've deleted all data related to this user, finally remove the
        # job from the queue.
        if self.remaining_rows_to_delete:
            self.job_queue_svc.delete([job])
            log.info("Complete 'delete_user' job %s", user.id)

    @property
    def remaining_rows_to_delete(self):
        return max(0, self.limit - self.num_rows_deleted)

    def delete_flags(self, user):
        return self.delete_rows(Flag, select(Flag.id).where(Flag.user_id == user.id))

    def delete_featurecohort_memberships(self, user):
        return self.delete_rows(
            FeatureCohortUser,
            select(FeatureCohortUser.id).where(FeatureCohortUser.user_id == user.id),
        )

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

    def delete_group_creators(self, user):
        if not self.remaining_rows_to_delete:
            return

        self.num_rows_deleted += self.db.execute(
            update(Group)
            .where(
                Group.id.in_(
                    select(
                        select(Group.id)
                        .where(Group.creator_id == user.id)
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
        if num_rows_deleted:
            log.info("Deleted %d rows from %s", num_rows_deleted, model_class)

        return deleted_ids


def service_factory(_context, request):
    return UserDeleteService(
        db=request.db,
        job_queue_svc=request.find_service(name="queue_service"),
        user_svc=request.find_service(name="user"),
    )
