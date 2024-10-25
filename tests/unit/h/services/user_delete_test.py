import logging
from datetime import datetime
from unittest.mock import call, sentinel

import pytest
from h_matchers import Any
from sqlalchemy import Select, func, inspect, select

from h.models import (
    Annotation,
    AuthTicket,
    FeatureCohortUser,
    Flag,
    Group,
    GroupMembership,
    GroupMembershipRoles,
    Job,
    Token,
    User,
    UserDeletion,
)
from h.services.user_delete import (
    LimitedWorker,
    LimitReached,
    UserDeleteService,
    UserPurger,
    service_factory,
)


class TestUserDeleteService:
    def test_delete_user(self, db_session, factories, svc):
        user, other_user, requested_by = factories.User.create_batch(3)
        user_annotations = factories.Annotation.create_batch(2, userid=user.userid)

        svc.delete_user(user, requested_by, "test_tag")

        assert user.deleted is True
        assert other_user.deleted is False
        assert db_session.scalars(select(Job)).all() == [
            Any.instance_of(Job).with_attrs(
                {
                    "name": "purge_user",
                    "priority": 0,
                    "tag": "UserDeleteService.delete_user",
                    "kwargs": {"userid": user.userid},
                }
            )
        ]
        assert (
            db_session.scalars(select(UserDeletion)).all()
            == Any.list.containing(
                [
                    Any.instance_of(UserDeletion).with_attrs(
                        {
                            "userid": user.userid,
                            "requested_by": requested_by.userid,
                            "tag": "test_tag",
                            "registered_date": user.registered_date,
                            "num_annotations": len(user_annotations),
                        }
                    )
                ]
            ).only()
        )

    def test_purge_deleted_users(
        self,
        db_session,
        factories,
        queue_service,
        svc,
        user_service,
        LimitedWorker,
        limited_worker,
        UserPurger,
        purger,
        caplog,
    ):
        users = factories.User.create_batch(3)
        user_service.fetch.side_effect = users
        jobs = [factories.Job(kwargs={"userid": user.userid}) for user in users]
        queue_service.get.return_value = jobs
        # Make UserPurger raise LimitReached part-way through purging
        # the third user, when delete_annotations() is called the third time.
        purger.delete_annotations.side_effect = [None, None, LimitReached]

        svc.purge_deleted_users()

        queue_service.get.assert_called_once_with("purge_user", 1000)
        LimitedWorker.assert_called_once_with(db_session, 1000)
        UserPurger.assert_called_once_with(db_session, queue_service, limited_worker)
        assert user_service.fetch.call_args_list == [
            call(user.userid) for user in users
        ]
        assert caplog.record_tuples == [
            (
                "h.services.user_delete",
                logging.INFO,
                f"Purging user: {user.userid}",
            )
            for user in users
        ]
        assert purger.delete_authtickets.call_args_list == [
            call(user) for user in users
        ]
        assert purger.delete_tokens.call_args_list == [call(user) for user in users]
        assert purger.delete_flags.call_args_list == [call(user) for user in users]
        assert purger.delete_featurecohort_memberships.call_args_list == [
            call(user) for user in users
        ]
        assert purger.delete_annotations.call_args_list == [
            call(user) for user in users
        ]
        assert purger.delete_groups.call_args_list == [call(user) for user in users[:2]]
        assert purger.delete_group_memberships.call_args_list == [
            call(user) for user in users[:2]
        ]
        assert purger.delete_group_creators.call_args_list == [
            call(user) for user in users[:2]
        ]
        assert purger.delete_user.call_args_list == [call(user) for user in users[:2]]
        queue_service.delete.assert_called_once_with(jobs[:2])

    def test_purge_deleted_users_with_no_jobs(
        self, svc, queue_service, caplog, LimitedWorker, UserPurger, user_service
    ):
        queue_service.get.return_value = []

        svc.purge_deleted_users()

        assert caplog.record_tuples == []
        LimitedWorker.assert_not_called()
        UserPurger.assert_not_called()
        user_service.fetch.assert_not_called()
        queue_service.delete.assert_not_called()

    def test_purge_deleted_users_with_an_invalid_job(
        self, svc, queue_service, caplog, factories
    ):
        invalid_job = factories.Job(kwargs={})  # No Job.kwargs["userid"].
        queue_service.get.return_value = [invalid_job]

        svc.purge_deleted_users()

        assert caplog.record_tuples == [
            (
                "h.services.user_delete",
                logging.INFO,
                f"Invalid 'JobName.PURGE_USER' job: {invalid_job!r}",
            )
        ]
        queue_service.delete.assert_called_once_with([invalid_job])

    def test_purge_deleted_users_when_a_jobs_user_doesnt_exist(
        self, svc, queue_service, user_service, caplog, factories
    ):
        job = factories.Job(kwargs={"userid": "doesnt_exist"})
        queue_service.get.return_value = [job]
        user_service.fetch.return_value = None

        svc.purge_deleted_users()

        assert caplog.record_tuples == [
            (
                "h.services.user_delete",
                logging.INFO,
                "Couldn't fetch user: doesnt_exist",
            )
        ]
        queue_service.delete.assert_called_once_with([job])

    @pytest.fixture(autouse=True)
    def UserPurger(self, mocker):
        return mocker.patch("h.services.user_delete.UserPurger")

    @pytest.fixture
    def purger(self, UserPurger):
        return UserPurger.return_value

    @pytest.fixture(autouse=True)
    def LimitedWorker(self, mocker):
        return mocker.patch("h.services.user_delete.LimitedWorker")

    @pytest.fixture
    def limited_worker(self, LimitedWorker):
        return LimitedWorker.return_value


class TestUserPurger:
    def test_delete_authtickets(self, worker, purger, factories, user, db_session):
        factories.AuthTicket.create_batch(2, user=user)
        # An AuthTicket belonging to another user. This shouldn't get deleted.
        other_ticket = factories.AuthTicket()

        purger.delete_authtickets(user)

        worker.delete.assert_called_once_with(AuthTicket, Any.instance_of(Select))
        assert db_session.scalars(select(AuthTicket)).all() == [other_ticket]

    def test_delete_tokens(self, worker, purger, factories, user, db_session):
        factories.DeveloperToken(user=user)
        factories.OAuth2Token(user=user)
        # Tokens belonging to other users. These shouldn't get deleted.
        other_tokens = [factories.DeveloperToken(), factories.OAuth2Token()]

        purger.delete_tokens(user)

        worker.delete.assert_called_once_with(Token, Any.instance_of(Select))
        assert (
            db_session.scalars(select(Token)).all()
            == Any.list.containing(other_tokens).only()
        )

    def test_delete_flags(self, worker, purger, factories, user, db_session):
        factories.Flag.create_batch(2, user=user)
        # A flag created by another user. This shouldn't get deleted.
        other_flag = factories.Flag()

        purger.delete_flags(user)

        worker.delete.assert_called_once_with(Flag, Any.instance_of(Select))
        assert db_session.scalars(select(Flag)).all() == [other_flag]

    def test_delete_featurecohort_memberships(
        self, worker, purger, user, factories, db_session
    ):
        cohorts = factories.FeatureCohort.create_batch(2, members=[user])
        # A FeatureCohortUser belonging to a different user.
        # This shouldn't get deleted.
        other_user = factories.User()
        cohorts[0].members.append(other_user)

        purger.delete_featurecohort_memberships(user)

        worker.delete.assert_called_once_with(
            FeatureCohortUser, Any.instance_of(Select)
        )
        assert db_session.scalars(select(FeatureCohortUser)).all() == [
            Any.instance_of(FeatureCohortUser).with_attrs(
                {"cohort_id": cohorts[0].id, "user_id": other_user.id}
            )
        ]

    def test_delete_annotations(
        self, caplog, worker, purger, user, factories, queue_service
    ):
        annotations = factories.Annotation.create_batch(2, userid=user.userid)
        annotation_slims = [
            factories.AnnotationSlim(annotation=annotation)
            for annotation in annotations
        ]
        # An annotation belonging to a different user.
        # This shouldn't get deleted.
        other_users_annotation = factories.Annotation()

        purger.delete_annotations(user)

        worker.update.assert_called_once_with(
            Annotation,
            Any.instance_of(Select),
            {"deleted": True, "updated": Any.instance_of(datetime)},
        )
        for annotation in annotations:
            assert annotation.deleted is True
        for annotation_slim in annotation_slims:
            assert annotation_slim.deleted is True
        assert other_users_annotation.deleted is False
        assert (
            queue_service.add_by_id.call_args_list
            == Any.list.containing(
                [
                    call(
                        name="sync_annotation",
                        annotation_id=annotation.id,
                        tag="UserDeleteService.delete_annotations",
                        schedule_in=60,
                    )
                    for annotation in annotations
                ]
            ).only()
        )
        assert (
            caplog.record_tuples
            == Any.list.containing(
                [
                    (
                        "h.services.user_delete",
                        logging.INFO,
                        "Updated 2 rows from annotation",
                    ),
                    (
                        "h.services.user_delete",
                        logging.INFO,
                        "Updated 2 rows from annotation_slim",
                    ),
                    (
                        "h.services.user_delete",
                        logging.INFO,
                        f"Enqueued jobs to delete {len(annotations)} annotations from Elasticsearch",
                    ),
                ]
            ).only()
        )

    def test_delete_groups(self, user, worker, factories, purger):
        def make_group(name, owner=user):
            """Create and return a group that `owner` is the only owner of."""
            return factories.Group(
                name=name,
                memberships=[
                    GroupMembership(user=owner, roles=[GroupMembershipRoles.OWNER])
                ],
            )

        # A list of groups that should be deleted when `user` is deleted.
        should_be_deleted = []

        # A group that `user` is the only owner of, this group should be
        # deleted when `user` is deleted.
        should_be_deleted.append(make_group("only_owner"))

        # A group that `user` is the only owner of but that has other non-owner
        # members. This group should still be deleted.
        group = make_group("other_members")
        for role in GroupMembershipRoles:
            if role == GroupMembershipRoles.OWNER:
                continue
            group.memberships.append(
                GroupMembership(user=factories.User(), roles=[role])
            )
        should_be_deleted.append(group)

        # A group that `user` is the only owner of but that contains a
        # deleted annotation by another user. This group should still be
        # deleted.
        group = make_group("deleted_annotation")
        factories.Annotation(group=group, deleted=True)
        should_be_deleted.append(group)

        # A list of groups that should *not* be deleted when `user` is deleted.
        should_not_be_deleted = []

        # A group that has one owner, but `user` isn't a member of this group.
        should_not_be_deleted.append(make_group("other_owner", owner=factories.User()))

        # Some groups that have one owner but `user` is a non-owner member.
        for role in GroupMembershipRoles:
            if role == GroupMembershipRoles.OWNER:
                continue
            group = make_group(role, owner=factories.User())
            group.memberships.append(GroupMembership(user=user, roles=[role]))
            should_not_be_deleted.append(group)

        # A group that `user` is an owner of but that also has another owner.
        group = make_group("another_owner")
        group.memberships.append(
            GroupMembership(user=factories.User(), roles=[GroupMembershipRoles.OWNER])
        )
        should_not_be_deleted.append(group)

        # A group that `user` is the only owner of but that contains an annotation from another user.
        group = make_group("annotation")
        factories.Annotation(group=group, deleted=False)
        should_not_be_deleted.append(group)

        purger.delete_groups(user)

        worker.delete.assert_called_once_with(Group, Any.instance_of(Select))
        for group in should_not_be_deleted:
            assert not inspect(group).deleted
        for group in should_be_deleted:
            assert inspect(group).deleted

    def test_delete_group_memberships(
        self, user, factories, purger, worker, db_session
    ):
        other_user = factories.User()
        groups = [
            # A group that `user` created.
            factories.Group(
                creator=user, memberships=[GroupMembership(user=other_user)]
            ),
            # A group that `user` is a member of but didn't create.
            factories.Group(
                memberships=[
                    GroupMembership(user=user),
                    GroupMembership(user=other_user),
                ]
            ),
            # A group that `user` is neither a creator or member of.
            factories.Group(memberships=[GroupMembership(user=other_user)]),
        ]

        purger.delete_group_memberships(user)

        worker.delete.assert_called_once_with(GroupMembership, Any.instance_of(Select))
        # It deletes the given user's group memberships.
        assert (
            db_session.scalars(
                select(GroupMembership).where(GroupMembership.user_id == user.id)
            ).all()
            == []
        )
        # It doesn't delete group memberships of other users.
        assert (
            db_session.scalars(
                select(GroupMembership).where(GroupMembership.user_id == other_user.id)
            ).all()
            == Any.list.containing(
                [
                    Any.instance_of(GroupMembership).with_attrs(
                        {"group_id": group.id, "user_id": other_user.id}
                    )
                    for group in groups
                ]
            ).only()
        )

    def test_delete_group_creators(self, user, factories, purger, worker):
        groups = factories.Group.create_batch(2, creator=user)
        other_group = factories.Group()

        purger.delete_group_creators(user)

        worker.update.assert_called_once_with(
            Group, Any.instance_of(Select), {"creator_id": None}
        )
        for group in groups:
            assert group.creator_id is None
        assert other_group.creator_id

    def test_delete_group_creators_doesnt_delete_other_group_creators(
        self, user, factories, purger
    ):
        other_group_creator = factories.User()
        group = factories.Group(creator=other_group_creator)

        purger.delete_group_creators(user)

        assert group.creator_id == other_group_creator.id

    def test_delete_user(self, db_session, purger, factories, user):
        other_user = factories.User()

        purger.delete_user(user)

        assert db_session.scalars(select(User)).all() == [other_user]

    @pytest.mark.parametrize(
        "method",
        [
            "delete_authtickets",
            "delete_tokens",
            "delete_flags",
            "delete_featurecohort_memberships",
            "delete_annotations",
            "delete_groups",
            "delete_group_memberships",
            "delete_group_creators",
            "delete_user",
        ],
    )
    def test_it_when_limit_exceeded(
        self, db_session, queue_service, mocker, factories, method
    ):
        worker = mocker.create_autospec(LimitedWorker, spec_set=True, instance=True)
        worker.delete.side_effect = LimitReached
        worker.update.side_effect = LimitReached
        purger = UserPurger(db_session, queue_service, worker)

        with pytest.raises(LimitReached):
            getattr(purger, method)(factories.User())

    @pytest.fixture
    def worker(self, db_session, mocker):
        worker = LimitedWorker(db_session, limit=1000)
        mocker.spy(worker, "delete")
        mocker.spy(worker, "update")
        return worker

    @pytest.fixture
    def purger(self, db_session, queue_service, worker):
        return UserPurger(db_session, queue_service, worker)

    @pytest.fixture
    def user(self, factories, db_session):
        user = factories.User()
        # Flush the DB to generate user.id.
        db_session.flush()
        return user


class TestLimitedWorker:
    def test_update(self, caplog, db_session, factories):
        annotations = factories.Annotation.create_batch(size=2, text="ORIGINAL")
        worker = LimitedWorker(db_session, limit=3)

        updated_annotation_ids = worker.update(
            Annotation, select(Annotation.id), {"text": "UPDATED"}
        )

        assert sorted(updated_annotation_ids) == sorted(
            [annotation.id for annotation in annotations]
        )
        assert worker.limit == 1
        for annotation in annotations:
            assert annotation.text == "UPDATED"
        assert caplog.record_tuples == [
            ("h.services.user_delete", logging.INFO, "Updated 2 rows from annotation")
        ]

    def test_update_when_no_matching_rows(self, caplog, db_session):
        worker = LimitedWorker(db_session, limit=3)

        updated_annotation_ids = worker.update(
            Annotation, select(Annotation.id), {"text": "UPDATED"}
        )

        assert updated_annotation_ids == []
        assert worker.limit == 3
        assert caplog.record_tuples == []

    def test_update_when_limit_exceeded(self, db_session, factories):
        annotation = factories.Annotation()
        original_text = annotation.text
        worker = LimitedWorker(db_session, limit=0)

        with pytest.raises(LimitReached):
            worker.update(Annotation, select(Annotation.id), {"text": "UPDATED"})

        # pylint:disable=use-implicit-booleaness-not-comparison-to-zero
        assert worker.limit == 0
        assert annotation.text == original_text

    def test_update_with_limit_remaining(self, caplog, db_session, factories):
        annotations = factories.Annotation.create_batch(2)
        original_limit = len(annotations) + 1
        worker = LimitedWorker(db_session, original_limit)

        updated_annotation_ids = worker.update(
            Annotation, select(Annotation.id), {"text": "UPDATED"}
        )

        assert sorted(updated_annotation_ids) == sorted(
            [annotation.id for annotation in annotations]
        )
        assert worker.limit == original_limit - len(updated_annotation_ids)
        for annotation in annotations:
            assert annotation.text == "UPDATED"
        assert caplog.record_tuples == [
            ("h.services.user_delete", logging.INFO, "Updated 2 rows from annotation")
        ]

    def test_update_when_limit_reached(self, caplog, db_session, factories):
        annotations = factories.Annotation.create_batch(2)
        original_limit = len(annotations) - 1
        worker = LimitedWorker(db_session, original_limit)

        updated_annotation_ids = worker.update(
            Annotation, select(Annotation.id), {"text": "UPDATED"}
        )

        assert len(updated_annotation_ids) == original_limit
        assert len(set(updated_annotation_ids)) == len(updated_annotation_ids)
        for updated_annotation_id in updated_annotation_ids:
            assert updated_annotation_id in [
                annotation.id for annotation in annotations
            ]
        # pylint:disable=use-implicit-booleaness-not-comparison-to-zero
        assert worker.limit == 0
        for annotation in annotations:
            if annotation.id in updated_annotation_ids:
                assert annotation.text == "UPDATED"
            else:
                assert annotation.text != "UPDATED"
        assert caplog.record_tuples == [
            ("h.services.user_delete", logging.INFO, "Updated 1 rows from annotation")
        ]

    def test_delete(self, caplog, db_session, factories):
        annotations = factories.Annotation.create_batch(size=2)
        worker = LimitedWorker(db_session, limit=3)

        deleted_annotation_ids = worker.delete(Annotation, select(Annotation.id))

        assert worker.limit == 1
        assert sorted(deleted_annotation_ids) == sorted(
            [annotation.id for annotation in annotations]
        )
        assert caplog.record_tuples == [
            ("h.services.user_delete", logging.INFO, "Deleted 2 rows from annotation")
        ]
        assert db_session.scalars(select(Annotation)).all() == []

    def test_delete_when_no_matching_rows(self, caplog, db_session):
        worker = LimitedWorker(db_session, limit=3)

        deleted_annotation_ids = worker.delete(Annotation, select(Annotation.id))

        assert worker.limit == 3
        assert deleted_annotation_ids == []
        assert caplog.record_tuples == []

    def test_delete_when_limit_exceeded(self, db_session, factories):
        annotation = factories.Annotation()
        worker = LimitedWorker(db_session, limit=0)

        with pytest.raises(LimitReached):
            worker.delete(Annotation, select(Annotation.id))

        # pylint:disable=use-implicit-booleaness-not-comparison-to-zero
        assert worker.limit == 0
        assert db_session.scalars(select(Annotation)).all() == [annotation]

    def test_delete_with_limit_remaining(self, caplog, db_session, factories):
        annotations = factories.Annotation.create_batch(2)
        original_limit = len(annotations) + 1
        worker = LimitedWorker(db_session, original_limit)

        deleted_annotation_ids = worker.delete(Annotation, select(Annotation.id))

        assert sorted(deleted_annotation_ids) == sorted(
            [annotation.id for annotation in annotations]
        )
        assert worker.limit == original_limit - len(deleted_annotation_ids)
        assert db_session.scalars(select(Annotation)).all() == []
        assert caplog.record_tuples == [
            ("h.services.user_delete", logging.INFO, "Deleted 2 rows from annotation")
        ]

    def test_delete_when_limit_reached(self, caplog, db_session, factories):
        annotations = factories.Annotation.create_batch(2)
        original_limit = len(annotations) - 1
        worker = LimitedWorker(db_session, original_limit)

        deleted_annotation_ids = worker.delete(Annotation, select(Annotation.id))

        assert len(deleted_annotation_ids) == original_limit
        assert len(set(deleted_annotation_ids)) == len(deleted_annotation_ids)
        for deleted_annotation_id in deleted_annotation_ids:
            assert deleted_annotation_id in [
                annotation.id for annotation in annotations
            ]
        # pylint:disable=use-implicit-booleaness-not-comparison-to-zero
        assert worker.limit == 0
        assert (
            db_session.scalar(select(func.count(Annotation.id)))
            == len(annotations) - original_limit
        )
        assert caplog.record_tuples == [
            ("h.services.user_delete", logging.INFO, "Deleted 1 rows from annotation")
        ]


class TestServiceFactory:
    def test_it(self, pyramid_request, UserDeleteService, queue_service, user_service):
        svc = service_factory(sentinel.context, pyramid_request)

        UserDeleteService.assert_called_once_with(
            pyramid_request.db,
            job_queue=queue_service,
            user_svc=user_service,
        )
        assert svc == UserDeleteService.return_value

    @pytest.fixture(autouse=True)
    def UserDeleteService(self, patch):
        return patch("h.services.user_delete.UserDeleteService")


@pytest.fixture
def svc(db_session, queue_service, user_service):
    return UserDeleteService(
        db_session,
        job_queue=queue_service,
        user_svc=user_service,
    )


@pytest.fixture
def caplog(caplog):
    caplog.set_level(logging.INFO)
    return caplog
