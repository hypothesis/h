from unittest.mock import sentinel

import pytest
from h_matchers import Any
from sqlalchemy import select

from h.models import Annotation, AuthTicket, Job, User
from h.services.user_expunge import UserExpungeService, factory


class TestUserExpungeService:
    def test_delete_user(self, db_session, svc, factories):
        user = factories.User()

        svc.delete_user(user.userid)

        assert db_session.scalars(select(Job)).all() == [
            Any.instance_of(Job).with_attrs(
                {
                    "name": "delete_user",
                    "priority": 0,
                    "tag": "h.tasks.enqueue_user_delete_job_to_queue",
                    "kwargs": {"userid": user.userid},
                }
            )
        ]

    def test_expunge_deleted_users(self, db_session, svc, factories, queue_service):
        user = factories.User()
        annotation = factories.Annotation(userid=user.userid)
        job = Job(
            name="delete_user",
            priority=0,
            tag="h.tasks.enqueue_user_delete_job_to_queue",
            kwargs={"userid": user.userid},
        )
        db_session.add(job)
        queue_service.get.return_value = [job]

        svc.expunge_deleted_users()

        queue_service.get.assert_called_once_with("delete_user", 1)
        # It should delete the annotations from the DB.
        assert db_session.execute(select(Annotation)).all() == []
        # It should queue tasks to delete the annotations from Elasticsearch.
        assert db_session.scalars(
            select(Job).where(Job.name == "delete_annotation")
        ).all() == [
            Any.instance_of(Job).with_attrs(
                {
                    "name": "delete_annotation",
                    "priority": 0,
                    "tag": "h.services.user_expunge.expunge_deleted_users",
                    "kwargs": {"annotation_id": annotation.id},
                }
            )
        ]
        # It should delete the user.
        assert db_session.execute(select(User)).all() == []
        # It should delete the job.
        assert (
            db_session.scalars(select(Job).where(Job.name == "delete_user")).all() == []
        )

    def test_expunge_delete_users_does_nothing_if_there_are_no_deleted_users(
        self, svc, queue_service
    ):
        queue_service.get.return_value = []

        svc.expunge_deleted_users()

    @pytest.mark.parametrize(
        "num_authtickets,limit,expected_deleted,expected_remaining",
        [
            (2, 2, 2, 0),
            (2, 1, 1, 1),
            (1, 2, 1, 0),
        ],
    )
    def test_delete_authtickets(
        self,
        db_session,
        factories,
        svc,
        num_authtickets,
        limit,
        expected_deleted,
        expected_remaining,
    ):
        user, other_user = factories.User.create_batch(2)
        db_session.flush()
        authtickets = factories.AuthTicket.create_batch(num_authtickets, user=user)
        other_authticket = factories.AuthTicket(user=other_user)
        svc.remaining_rows_to_delete = limit

        svc.delete_rows(
            AuthTicket, select(AuthTicket.id).where(AuthTicket.user_id == user.id)
        )

        assert (
            db_session.scalars(select(AuthTicket)).all()
            == Any.list.containing(
                [
                    other_authticket,
                    *[
                        Any.object.of_type(AuthTicket).with_attrs({"user_id": user.id})
                        for _ in range(expected_remaining)
                    ],
                ]
            ).only()
        )
        assert svc.remaining_rows_to_delete == min(0, limit - expected_deleted)

    @pytest.fixture(autouse=True)
    def svc(self, db_session, queue_service, user_service):
        return UserExpungeService(
            db=db_session,
            job_queue_svc=queue_service,
            user_service=user_service,
        )


class TestFactory:
    def test_it(self, UserExpungeService, pyramid_request, queue_service):
        svc = factory(sentinel.context, pyramid_request)

        UserExpungeService.assert_called_once_with(pyramid_request.db, queue_service)
        assert svc == UserExpungeService.return_value

    @pytest.fixture(autouse=True)
    def UserExpungeService(self, patch):
        return patch("h.services.user_expunge.UserExpungeService")
