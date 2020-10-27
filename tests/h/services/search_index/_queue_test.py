import datetime as datetime_
import uuid
from unittest import mock
from unittest.mock import patch, sentinel

import factory
import pytest
from h_matchers import Any
from sqlalchemy.sql.elements import BinaryExpression

from h.db.types import URLSafeUUID
from h.models import Annotation, Job
from h.search.index import BatchIndexer
from h.services.search_index import SearchIndexService
from h.services.search_index._queue import Queue

LIMIT = 2
ONE_WEEK = datetime_.timedelta(weeks=1)
ONE_WEEK_IN_SECONDS = int(ONE_WEEK.total_seconds())
MINUS_5_MIN = datetime_.timedelta(minutes=-5)
MINUS_5_MIN_IN_SECS = int(MINUS_5_MIN.total_seconds())


class TestQueue:
    def test_add_where(self, queue, factories, db_session, now):
        matching = [
            factories.Annotation.create(shared=True),
            factories.Annotation.create(shared=True),
        ]
        # Add some noise
        factories.Annotation.create(shared=False)

        queue.add_where(
            where=[Annotation.shared.is_(True)],
            tag="test_tag",
            priority=1234,
            schedule_in=ONE_WEEK_IN_SECONDS,
        )

        assert db_session.query(Job).all() == [
            Any.instance_of(Job).with_attrs(
                dict(
                    enqueued_at=Any.instance_of(datetime_.datetime),
                    scheduled_at=now + ONE_WEEK,
                    tag="test_tag",
                    priority=1234,
                    kwargs={
                        "annotation_id": self.database_id(annotation),
                        "force": False,
                    },
                )
            )
            for annotation in matching
        ]

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
        annotation = factories.Annotation.create()

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

    def database_id(self, annotation):
        """Return `annotation.id` in the internal format used within the database."""
        return str(uuid.UUID(URLSafeUUID.url_safe_to_hex(annotation.id)))

    @pytest.fixture()
    def add_where(self, queue):
        with patch.object(queue, "add_where") as add_where:
            yield add_where


class TestSync:
    def test_it_does_nothing_if_the_queue_is_empty(self, batch_indexer, queue):
        queue.sync(LIMIT)

        batch_indexer.index.assert_not_called()

    def test_it_ignores_jobs_that_arent_scheduled_yet(
        self, add_all, batch_indexer, queue
    ):
        add_all(schedule_in=ONE_WEEK_IN_SECONDS)

        queue.sync(LIMIT)

        batch_indexer.index.assert_not_called()

    @pytest.mark.usefixtures("with_queued_annotations")
    def test_it_ignores_jobs_beyond_limit(
        self, all_annotation_ids, batch_indexer, queue
    ):
        queue.sync(LIMIT)

        for annotation_id in all_annotation_ids[LIMIT:]:
            assert annotation_id not in batch_indexer.index.call_args[0][0]

    def test_it_ignores_jobs_that_are_expired(
        self, batch_indexer, db_session, factories, now, queue, LOG
    ):
        annotation = factories.Annotation()
        queue.add_by_id(annotation.id, "test_tag", schedule_in=MINUS_5_MIN_IN_SECS)
        # Change the job's expires_at date so that it's expired.
        job = db_session.query(Job).one()
        job.expires_at = now - datetime_.timedelta(minutes=1)

        queue.sync(LIMIT)

        batch_indexer.index.assert_not_called()
        assert db_session.query(Job).all() == [job]

    @pytest.mark.usefixtures("with_indexed_annotations")
    def test_if_the_job_has_force_True_it_indexes_the_annotation_and_deletes_the_job(
        self, annotation_ids, add_all, batch_indexer, db_session, queue, LOG
    ):
        add_all(force=True)

        queue.sync(LIMIT)

        LOG.info.assert_called_with({Queue.Result.FORCED: LIMIT})
        assert db_session.query(Job).all() == []
        batch_indexer.index.assert_called_once_with(
            Any.list.containing(annotation_ids).only()
        )

    def test_if_the_annotation_isnt_in_the_DB_it_deletes_the_job_from_the_queue(
        self, annotations, add_all, db_session, queue, LOG
    ):
        for annotation in annotations:
            db_session.delete(annotation)

        add_all()

        queue.sync(LIMIT)

        LOG.info.assert_called_with({Queue.Result.DELETED_FROM_DB: LIMIT})
        assert db_session.query(Job).all() == []

    def test_if_the_annotation_is_marked_as_deleted_in_the_DB_it_deletes_the_job_from_the_queue(
        self, annotations, add_all, db_session, queue, LOG
    ):
        for annotation in annotations:
            annotation.deleted = True

        add_all()

        queue.sync(LIMIT)

        LOG.info.assert_called_with({Queue.Result.DELETED_FROM_DB: LIMIT})
        assert db_session.query(Job).all() == []

    @pytest.mark.usefixtures("with_queued_annotations")
    def test_if_the_annotation_is_missing_from_Elastic_it_indexes_it(
        self, annotation_ids, batch_indexer, queue, LOG
    ):
        queue.sync(LIMIT)

        LOG.info.assert_called_with({Queue.Result.MISSING: LIMIT})
        batch_indexer.index.assert_called_once_with(
            Any.list.containing(annotation_ids).only()
        )

    @pytest.mark.usefixtures("with_indexed_annotations", "with_queued_annotations")
    def test_if_the_annotation_is_already_in_Elastic_it_removes_the_job_from_the_queue(
        self, batch_indexer, db_session, queue, LOG
    ):
        queue.sync(LIMIT)

        LOG.info.assert_called_with({Queue.Result.UP_TO_DATE: LIMIT})
        assert db_session.query(Job).all() == []
        batch_indexer.index.assert_not_called()

    @pytest.mark.usefixtures("with_indexed_annotations", "with_queued_annotations")
    def test_if_the_annotation_has_a_different_updated_time_in_Elastic_it_indexes_it(
        self, annotations, annotation_ids, batch_indexer, now, queue, LOG
    ):
        # Simulate the annotations having been updated in the DB after they
        # were indexed.
        for annotation in annotations:
            annotation.updated = now

        queue.sync(LIMIT)

        LOG.info.assert_called_with({Queue.Result.DIFFERENT: LIMIT})
        batch_indexer.index.assert_called_once_with(
            Any.list.containing(annotation_ids).only()
        )

    @pytest.mark.usefixtures("with_indexed_annotations", "with_queued_annotations")
    def test_if_the_annotation_has_a_different_userid_in_Elastic_it_indexes_it(
        self, annotations, annotation_ids, batch_indexer, queue, LOG
    ):
        # Simulate the user having been renamed in the DB.
        for annotation in annotations:
            annotation.userid = "new_userid"

        queue.sync(LIMIT)

        LOG.info.assert_called_with({Queue.Result.DIFFERENT: LIMIT})
        batch_indexer.index.assert_called_once_with(
            Any.list.containing(annotation_ids).only()
        )

    def test_if_there_are_multiple_jobs_with_the_same_annotation_id(
        self, annotation_ids, batch_indexer, add_all, queue, LOG
    ):
        add_all(ids=[annotation_ids[0] for _ in range(LIMIT)])
        queue.sync(LIMIT)

        # It only syncs the annotation to Elasticsearch once.
        LOG.info.assert_called_with({Queue.Result.MISSING: LIMIT})
        batch_indexer.index.assert_called_once_with(
            Any.list.containing([annotation_ids[0]]).only()
        )

    def test_deleting_multiple_jobs_with_the_same_annotation_id(
        self, annotations, batch_indexer, add_all, db_session, index, queue, LOG
    ):
        add_all(ids=[annotations[0].id for _ in range(LIMIT)])
        index([annotations[0]])

        queue.sync(LIMIT)

        LOG.info.assert_called_with({Queue.Result.UP_TO_DATE: LIMIT})
        assert db_session.query(Job).all() == []
        batch_indexer.index.assert_not_called()

    @pytest.fixture
    def annotations(self, factories, now):
        return factories.Annotation.create_batch(
            size=LIMIT + 1,  # Make sure there's always over the limit
            created=now - datetime_.timedelta(minutes=1),
            updated=now - datetime_.timedelta(minutes=1),
        )

    @pytest.fixture
    def all_annotation_ids(self, annotations):
        return [annotation.id for annotation in annotations]

    @pytest.fixture
    def annotation_ids(self, all_annotation_ids):
        return all_annotation_ids[:LIMIT]

    @pytest.fixture
    def search_index(
        self, es_client, pyramid_request, moderation_service, nipsa_service
    ):
        return SearchIndexService(
            pyramid_request,
            es_client,
            session=pyramid_request.db,
            settings={},
            queue=queue,
        )

    @pytest.fixture
    def with_indexed_annotations(self, index, annotations):
        index(annotations)

    @pytest.fixture
    def with_queued_annotations(self, add_all):
        add_all()

    @pytest.fixture
    def index(self, es_client, search_index, nipsa_service):
        """A function for adding annotations to Elasticsearch."""

        def index(annotations):
            """Add `annotations` to the Elasticsearch index."""
            for annotation in annotations:
                search_index.add_annotation(annotation)

            es_client.conn.indices.refresh(index=es_client.index)

        return index

    @pytest.fixture
    def add_all(self, queue, annotation_ids):
        def add_all(ids=annotation_ids, schedule_in=MINUS_5_MIN_IN_SECS, force=False):
            for id_ in ids:
                queue.add_by_id(
                    id_, tag="test_tag", schedule_in=schedule_in, force=force
                )

        return add_all


class TestCount:
    def test_it(self, db_session, factories, now, queue):
        one_minute = datetime_.timedelta(minutes=1)

        class JobFactory(factories.Job):
            """A factory that, by default, creates jobs that should be counted."""

            name = "sync_annotation"
            tag = factory.Iterator(
                ["storage.create_annotation", "storage.update_annotation"]
            )
            scheduled_at = now - one_minute

        # 2 jobs that should be counted.
        JobFactory.create_batch(size=2)
        # A job that shouldn't be counted because it has the wrong tag.
        JobFactory.create(tag="wrong_tag")
        # A job that shouldn't be counted because it has the wrong name.
        JobFactory.create(name="wrong_name")
        # A job that shouldn't be counted because it's expired.
        JobFactory.create(expires_at=now - one_minute)
        # A job that shouldn't be counted because it isn't scheduled yet.
        JobFactory.create(scheduled_at=now + one_minute)

        count = queue.count(["storage.create_annotation", "storage.update_annotation"])

        assert count == 2


@pytest.fixture
def batch_indexer():
    return mock.create_autospec(BatchIndexer, spec_set=True, instance=True)


@pytest.fixture(autouse=True)
def datetime(patch, now):
    datetime = patch("h.services.search_index._queue.datetime")
    datetime.utcnow.return_value = now
    return datetime


@pytest.fixture(autouse=True)
def LOG(patch):
    return patch("h.services.search_index._queue.LOG")


@pytest.fixture
def now():
    return datetime_.datetime.utcnow()


@pytest.fixture
def queue(batch_indexer, db_session, es_client):
    return Queue(db_session, es_client, batch_indexer)
