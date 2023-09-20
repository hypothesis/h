import datetime as datetime_
import uuid
from unittest import mock
from unittest.mock import patch, sentinel

import pytest
from h_matchers import Any
from sqlalchemy.sql.elements import BinaryExpression

from h.db.types import URLSafeUUID
from h.models import Annotation, Job
from h.search.index import BatchIndexer
from h.services.search_index import SearchIndexService
from h.services.search_index._queue import Queue

ONE_WEEK = datetime_.timedelta(weeks=1)
ONE_WEEK_IN_SECONDS = int(ONE_WEEK.total_seconds())
MINUS_5_MIN = datetime_.timedelta(minutes=-5)
MINUS_5_MIN_IN_SECS = int(MINUS_5_MIN.total_seconds())


pytestmark = [
    pytest.mark.xdist_group("elasticsearch"),
    pytest.mark.usefixtures("init_elasticsearch"),
]


class TestQueue:
    def test_add_where(self, queue, factories, db_session, now):
        matching = [
            factories.Annotation(shared=True),
            factories.Annotation(shared=True),
        ]
        # Add some noise
        factories.Annotation(shared=False)

        queue.add_where(
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
                            "enqueued_at": Any.instance_of(datetime_.datetime),
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
        self, queue, db_session, factories, force, expected_force
    ):
        annotation = factories.Annotation()

        queue.add_where([Annotation.id == annotation.id], "test_tag", 1, force=force)

        assert db_session.query(Job).one().kwargs["force"] == expected_force

    def test_add_by_id(self, queue, add_where):
        queue.add_by_id(
            sentinel.annotation_id,
            sentinel.tag,
            schedule_in=sentinel.schedule_in,
            force=sentinel.force,
        )

        add_where.assert_called_once_with(
            [Any.instance_of(BinaryExpression)],
            sentinel.tag,
            Queue.Priority.SINGLE_ITEM,
            sentinel.force,
            sentinel.schedule_in,
        )

        where = add_where.call_args[0][0]
        assert where[0].compare(Annotation.id == sentinel.annotation_id)

    def test_add_annotations_between_times(self, queue, add_where):
        queue.add_between_times(
            sentinel.start_time, sentinel.end_time, sentinel.tag, force=sentinel.force
        )

        add_where.assert_called_once_with(
            [Any.instance_of(BinaryExpression)] * 2,
            sentinel.tag,
            Queue.Priority.BETWEEN_TIMES,
            sentinel.force,
        )

        where = add_where.call_args[0][0]
        assert where[0].compare(Annotation.updated >= sentinel.start_time)
        assert where[1].compare(Annotation.updated <= sentinel.end_time)

    def test_add_users_annotations(self, queue, add_where):
        queue.add_by_user(
            sentinel.userid,
            sentinel.tag,
            force=sentinel.force,
            schedule_in=sentinel.schedule_in,
        )

        add_where.assert_called_once_with(
            [Any.instance_of(BinaryExpression)],
            sentinel.tag,
            Queue.Priority.SINGLE_USER,
            sentinel.force,
            sentinel.schedule_in,
        )

        where = add_where.call_args[0][0]
        assert where[0].compare(Annotation.userid == sentinel.userid)

    def test_add_group_annotations(self, queue, add_where):
        queue.add_by_group(
            sentinel.groupid,
            sentinel.tag,
            force=sentinel.force,
            schedule_in=sentinel.schedule_in,
        )

        add_where.assert_called_once_with(
            [Any.instance_of(BinaryExpression)],
            sentinel.tag,
            Queue.Priority.SINGLE_GROUP,
            sentinel.force,
            sentinel.schedule_in,
        )

        where = add_where.call_args[0][0]
        assert where[0].compare(Annotation.groupid == sentinel.groupid)

    def database_id(self, annotation):
        """Return `annotation.id` in the internal format used within the database."""
        return str(uuid.UUID(URLSafeUUID.url_safe_to_hex(annotation.id)))

    @pytest.fixture()
    def add_where(self, queue):
        with patch.object(queue, "add_where") as add_where:
            yield add_where


class TestSync:
    def test_it_does_nothing_if_the_queue_is_empty(self, batch_indexer, queue):
        counts = queue.sync(1)

        assert counts == {}
        batch_indexer.index.assert_not_called()

    def test_it_ignores_jobs_that_arent_scheduled_yet(
        self, batch_indexer, factories, now, queue
    ):
        factories.SyncAnnotationJob(scheduled_at=now + datetime_.timedelta(hours=1))

        counts = queue.sync(1)

        assert counts == {}
        batch_indexer.index.assert_not_called()

    def test_it_ignores_jobs_beyond_limit(self, batch_indexer, factories, queue):
        limit = 1
        factories.SyncAnnotationJob.create_batch(size=limit + 1)

        queue.sync(limit)

        assert len(batch_indexer.index.call_args[0][0]) == limit

    def test_it_ignores_jobs_that_are_expired(
        self, batch_indexer, db_session, factories, now, queue
    ):
        job = factories.SyncAnnotationJob(expires_at=now - datetime_.timedelta(hours=1))

        counts = queue.sync(1)

        assert counts == {}
        batch_indexer.index.assert_not_called()
        assert job in db_session.query(Job)

    def test_if_the_job_has_force_True_it_indexes_the_annotation_and_deletes_the_job(
        self, batch_indexer, db_session, factories, queue
    ):
        job = factories.SyncAnnotationJob(force=True)

        counts = queue.sync(1)

        assert counts == {
            Queue.Result.SYNCED_FORCED.format(tag="test_tag"): 1,
            Queue.Result.SYNCED_TAG_TOTAL.format(tag="test_tag"): 1,
            Queue.Result.SYNCED_TOTAL: 1,
            Queue.Result.COMPLETED_FORCED.format(tag="test_tag"): 1,
            Queue.Result.COMPLETED_TAG_TOTAL.format(tag="test_tag"): 1,
            Queue.Result.COMPLETED_TOTAL: 1,
        }
        assert job not in db_session.query(Job)
        batch_indexer.index.assert_called_once_with([self.url_safe_id(job)])

    def test_if_the_annotation_isnt_in_the_DB_it_deletes_the_job_from_the_queue(
        self, db_session, factories, queue
    ):
        # We have to actually create an annotation and save it to the DB in
        # order to get a valid annotation ID. Then we delete the annotation
        # from the DB again because we actually don't want the annotation to be
        # in the DB in this test.
        annotation = factories.Annotation()
        job = factories.SyncAnnotationJob(annotation=annotation)
        db_session.delete(annotation)

        counts = queue.sync(1)

        assert counts == {
            Queue.Result.COMPLETED_DELETED.format(tag="test_tag"): 1,
            Queue.Result.COMPLETED_TAG_TOTAL.format(tag="test_tag"): 1,
            Queue.Result.COMPLETED_TOTAL: 1,
        }
        assert job not in db_session.query(Job)

    def test_if_the_annotation_is_marked_as_deleted_in_the_DB_it_deletes_the_job_from_the_queue(
        self, db_session, factories, queue
    ):
        annotation = factories.Annotation()
        job = factories.SyncAnnotationJob(annotation=annotation)
        annotation.deleted = True

        counts = queue.sync(1)

        assert counts == {
            Queue.Result.COMPLETED_DELETED.format(tag="test_tag"): 1,
            Queue.Result.COMPLETED_TAG_TOTAL.format(tag="test_tag"): 1,
            Queue.Result.COMPLETED_TOTAL: 1,
        }
        assert job not in db_session.query(Job)

    def test_if_the_annotation_is_missing_from_Elastic_it_indexes_it(
        self, batch_indexer, factories, queue
    ):
        job = factories.SyncAnnotationJob()

        counts = queue.sync(1)

        assert counts == {
            Queue.Result.SYNCED_MISSING.format(tag="test_tag"): 1,
            Queue.Result.SYNCED_TAG_TOTAL.format(tag="test_tag"): 1,
            Queue.Result.SYNCED_TOTAL: 1,
        }
        batch_indexer.index.assert_called_once_with([self.url_safe_id(job)])

    def test_if_the_annotation_is_already_in_Elastic_it_removes_the_job_from_the_queue(
        self, batch_indexer, db_session, factories, index, queue
    ):
        annotation = factories.Annotation()
        index(annotation)
        job = factories.SyncAnnotationJob(annotation=annotation)

        counts = queue.sync(1)

        assert counts == {
            Queue.Result.COMPLETED_UP_TO_DATE.format(tag="test_tag"): 1,
            Queue.Result.COMPLETED_TAG_TOTAL.format(tag="test_tag"): 1,
            Queue.Result.COMPLETED_TOTAL: 1,
        }
        assert job not in db_session.query(Job)
        batch_indexer.index.assert_not_called()

    def test_if_the_annotation_has_a_different_updated_time_in_Elastic_it_indexes_it(
        self, batch_indexer, factories, index, now, queue
    ):
        annotation = factories.Annotation()
        index(annotation)
        factories.SyncAnnotationJob(annotation=annotation)
        # Simulate the annotation having been updated in the DB after it was
        # indexed.
        annotation.updated = now

        counts = queue.sync(1)

        assert counts == {
            Queue.Result.SYNCED_DIFFERENT.format(tag="test_tag"): 1,
            Queue.Result.SYNCED_TAG_TOTAL.format(tag="test_tag"): 1,
            Queue.Result.SYNCED_TOTAL: 1,
        }
        batch_indexer.index.assert_called_once_with([annotation.id])

    def test_if_the_annotation_has_a_different_userid_in_Elastic_it_indexes_it(
        self, batch_indexer, factories, index, queue
    ):
        annotation = factories.Annotation()
        index(annotation)
        factories.SyncAnnotationJob(annotation=annotation)
        # Simulate the user having been renamed in the DB.
        annotation.userid = "new_userid"

        counts = queue.sync(1)

        assert counts == {
            Queue.Result.SYNCED_DIFFERENT.format(tag="test_tag"): 1,
            Queue.Result.SYNCED_TAG_TOTAL.format(tag="test_tag"): 1,
            Queue.Result.SYNCED_TOTAL: 1,
        }
        batch_indexer.index.assert_called_once_with([annotation.id])

    def test_if_there_are_multiple_jobs_with_the_same_annotation_id(
        self, batch_indexer, factories, queue
    ):
        annotation = factories.Annotation()
        jobs = factories.SyncAnnotationJob.create_batch(size=2, annotation=annotation)

        counts = queue.sync(len(jobs))

        assert counts == {
            Queue.Result.SYNCED_MISSING.format(tag="test_tag"): 1,
            Queue.Result.SYNCED_TAG_TOTAL.format(tag="test_tag"): 1,
            Queue.Result.SYNCED_TOTAL: 1,
        }
        # It only syncs the annotation to Elasticsearch once, even though it
        # processed two separate jobs (for the same annotation).
        batch_indexer.index.assert_called_once_with([annotation.id])

    def test_deleting_multiple_jobs_with_the_same_annotation_id(
        self, batch_indexer, db_session, factories, index, queue
    ):
        annotation = factories.Annotation()
        index(annotation)
        jobs = factories.SyncAnnotationJob.create_batch(size=2, annotation=annotation)

        counts = queue.sync(len(jobs))

        assert counts == {
            Queue.Result.COMPLETED_UP_TO_DATE.format(tag="test_tag"): 2,
            Queue.Result.COMPLETED_TAG_TOTAL.format(tag="test_tag"): 2,
            Queue.Result.COMPLETED_TOTAL: 2,
        }
        for job in jobs:
            assert job not in db_session.query(Job)
        batch_indexer.index.assert_not_called()

    def test_metrics(self, factories, index, now, queue):
        def add_job(indexed=True, updated=False, deleted=False, **kwargs):
            annotation = factories.Annotation()
            factories.SyncAnnotationJob(annotation=annotation, **kwargs)

            if indexed:
                index(annotation)

            if updated:
                annotation.updated = now + ONE_WEEK

            if deleted:
                annotation.deleted = True

        add_job()
        add_job(indexed=False)
        add_job(updated=True)
        add_job(deleted=True)
        add_job(tag="tag_2", force=True)

        counts = queue.sync(5)

        assert counts == {
            "Synced/Total": 3,
            "Completed/Total": 3,
            "Synced/test_tag/Total": 2,
            "Completed/test_tag/Total": 2,
            "Synced/test_tag/Different_in_Elastic": 1,
            "Synced/test_tag/Missing_from_Elastic": 1,
            "Synced/tag_2/Forced": 1,
            "Synced/tag_2/Total": 1,
            "Completed/tag_2/Forced": 1,
            "Completed/tag_2/Total": 1,
            "Completed/test_tag/Up_to_date_in_Elastic": 1,
            "Completed/test_tag/Deleted_from_db": 1,
        }

    def url_safe_id(self, job):
        """Return the URL-safe version of the given job's annotation ID."""
        return URLSafeUUID.hex_to_url_safe(job.kwargs["annotation_id"])

    @pytest.fixture
    def search_index(
        self,
        es_client,
        pyramid_request,
        moderation_service,
        nipsa_service,
        annotation_read_service,
    ):  # pylint:disable=unused-argument
        return SearchIndexService(
            pyramid_request,
            es_client,
            session=pyramid_request.db,
            settings={},
            queue=queue,
            annotation_read_service=annotation_read_service,
        )

    @pytest.fixture
    def index(self, es_client, search_index):
        """Declare a method that indexes the given annotation into Elasticsearch."""

        def index(annotation):
            search_index.add_annotation(annotation)
            es_client.conn.indices.refresh(index=es_client.index)

        return index

    @pytest.fixture(autouse=True)
    def noise_annotations(self, factories, index):
        # Create some noise annotations in the DB. Some of them also in
        # Elasticsearch, some not. None of these should ever be touched by the
        # sync() method in these tests.
        annotations = factories.Annotation.create_batch(size=2)
        index(annotations[0])

    @pytest.fixture(autouse=True)
    def noise_jobs(self, factories):
        # Create some noise jobs in the DB. None of these should ever be
        # touched by the sync() method in these tests.
        factories.Job()


@pytest.fixture
def batch_indexer():
    return mock.create_autospec(BatchIndexer, spec_set=True, instance=True)


@pytest.fixture(autouse=True)
def datetime(patch, now):
    datetime = patch("h.services.search_index._queue.datetime")
    datetime.utcnow.return_value = now
    return datetime


@pytest.fixture
def now():
    return datetime_.datetime.utcnow()


@pytest.fixture
def queue(batch_indexer, db_session, es_client):
    return Queue(db_session, es_client, batch_indexer)
