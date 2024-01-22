import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, sentinel

import pytest
from freezegun import freeze_time
from h_matchers import Any
from sqlalchemy.sql.expression import BinaryExpression

from h.db.types import URLSafeUUID
from h.models import Annotation, Job
from h.services.job_queue import JobQueueService, Priority, factory

ONE_WEEK = timedelta(weeks=1)
ONE_WEEK_IN_SECONDS = int(ONE_WEEK.total_seconds())


class TestQueueService:
    def test_get_ignores_jobs_that_are_expired(self, factories, svc):
        now = datetime.utcnow()

        factories.SyncAnnotationJob(expires_at=now - timedelta(hours=1))

        assert not svc.get("sync_annotation", limit=100)

    def test_it_ignores_jobs_that_arent_scheduled_yet(self, factories, svc):
        now = datetime.utcnow()
        factories.SyncAnnotationJob(scheduled_at=now + timedelta(hours=1))

        assert not svc.get("sync_annotation", limit=100)

    def test_it_ignores_jobs_beyond_limit(self, factories, svc):
        limit = 1
        factories.SyncAnnotationJob.create_batch(size=limit + 1)

        jobs = svc.get("sync_annotation", limit=limit)

        assert len(jobs) == limit

    @freeze_time("2023-01-01")
    def test_add_where(self, factories, db_session, svc):
        now = datetime.utcnow()
        matching = [
            factories.Annotation(shared=True),
            factories.Annotation(shared=True),
        ]
        # Add some noise
        factories.Annotation(shared=False)

        svc.add_where(
            "sync_annotation",
            where=[Annotation.shared.is_(True)],
            tag="test_tag",
            priority=1234,
            schedule_in=ONE_WEEK_IN_SECONDS,
        )

        assert (
            db_session.query(Job).all()
            == Any.list.containing(
                [
                    Any.instance_of(Job).with_attrs(
                        {
                            "enqueued_at": Any.instance_of(datetime),
                            "scheduled_at": now + ONE_WEEK,
                            "tag": "test_tag",
                            "priority": 1234,
                            "kwargs": {
                                "annotation_id": self.database_id(annotation),
                                "force": False,
                            },
                        }
                    )
                    for annotation in matching
                ]
            ).only()
        )

    @pytest.mark.parametrize(
        "force,expected_force",
        (
            (True, True),
            (1, True),
            (False, False),
            ("", False),
        ),
    )
    def test_add_where_with_force(
        self, db_session, factories, force, expected_force, svc
    ):
        annotation = factories.Annotation()

        svc.add_where(
            "sync_annotation",
            [Annotation.id == annotation.id],
            "test_tag",
            1,
            force=force,
        )

        assert db_session.query(Job).one().kwargs["force"] == expected_force

    def test_add_by_id(self, svc, add_where):
        svc.add_by_id(
            sentinel.name,
            sentinel.annotation_id,
            sentinel.tag,
            schedule_in=sentinel.schedule_in,
            force=sentinel.force,
        )

        add_where.assert_called_once_with(
            sentinel.name,
            [Any.instance_of(BinaryExpression)],
            sentinel.tag,
            Priority.SINGLE_ITEM,
            sentinel.force,
            sentinel.schedule_in,
        )

        where = add_where.call_args[0][1]
        assert where[0].compare(Annotation.id == sentinel.annotation_id)

    def test_add_annotations_between_times(self, svc, add_where):
        svc.add_between_times(
            sentinel.name,
            sentinel.start_time,
            sentinel.end_time,
            sentinel.tag,
            force=sentinel.force,
        )

        add_where.assert_called_once_with(
            sentinel.name,
            [Any.instance_of(BinaryExpression)] * 2,
            sentinel.tag,
            Priority.BETWEEN_TIMES,
            sentinel.force,
        )

        where = add_where.call_args[0][1]
        assert where[0].compare(Annotation.updated >= sentinel.start_time)
        assert where[1].compare(Annotation.updated <= sentinel.end_time)

    def test_add_users_annotations(self, svc, add_where):
        svc.add_by_user(
            sentinel.name,
            sentinel.userid,
            sentinel.tag,
            force=sentinel.force,
            schedule_in=sentinel.schedule_in,
        )

        add_where.assert_called_once_with(
            sentinel.name,
            [Any.instance_of(BinaryExpression)],
            sentinel.tag,
            Priority.SINGLE_USER,
            sentinel.force,
            sentinel.schedule_in,
        )

        where = add_where.call_args[0][1]
        assert where[0].compare(Annotation.userid == sentinel.userid)

    def test_add_group_annotations(self, svc, add_where):
        svc.add_by_group(
            sentinel.name,
            sentinel.groupid,
            sentinel.tag,
            force=sentinel.force,
            schedule_in=sentinel.schedule_in,
        )

        add_where.assert_called_once_with(
            sentinel.name,
            [Any.instance_of(BinaryExpression)],
            sentinel.tag,
            Priority.SINGLE_GROUP,
            sentinel.force,
            sentinel.schedule_in,
        )

        where = add_where.call_args[0][1]
        assert where[0].compare(Annotation.groupid == sentinel.groupid)

    def test_delete(self, factories, svc, db_session):
        jobs = factories.SyncAnnotationJob.create_batch(size=5)
        db_session.flush()

        svc.delete(jobs)

        assert not db_session.query(Job).all()

    def test_factory(self, pyramid_request, db_session):
        svc = factory(sentinel.context, pyramid_request)

        assert svc._db == db_session  # pylint:disable=protected-access

    def database_id(self, annotation):
        """Return `annotation.id` in the internal format used within the database."""
        return str(uuid.UUID(URLSafeUUID.url_safe_to_hex(annotation.id)))

    @pytest.fixture()
    def add_where(self, svc):
        with patch.object(svc, "add_where") as add_where:
            yield add_where

    @pytest.fixture()
    def svc(self, db_session):
        return JobQueueService(db_session)
