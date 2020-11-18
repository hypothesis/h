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

ONE_WEEK = datetime_.timedelta(weeks=1)
ONE_WEEK_IN_SECONDS = int(ONE_WEEK.total_seconds())
MINUS_5_MIN = datetime_.timedelta(minutes=-5)
MINUS_5_MIN_IN_SECS = int(MINUS_5_MIN.total_seconds())


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
        self, batch_indexer, now, queue, SyncAnnotationJobFactory
    ):
        SyncAnnotationJobFactory(scheduled_at=now + datetime_.timedelta(hours=1))

        counts = queue.sync(1)

        assert counts == {}
        batch_indexer.index.assert_not_called()

    def test_it_ignores_jobs_beyond_limit(
        self, batch_indexer, queue, SyncAnnotationJobFactory
    ):
        limit = 1
        SyncAnnotationJobFactory.create_batch(size=limit + 1)

        queue.sync(limit)

        assert len(batch_indexer.index.call_args[0][0]) == limit

    def test_it_ignores_jobs_that_are_expired(
        self, batch_indexer, db_session, now, queue, SyncAnnotationJobFactory
    ):
        job = SyncAnnotationJobFactory(expires_at=now - datetime_.timedelta(hours=1))

        counts = queue.sync(1)

        assert counts == {}
        batch_indexer.index.assert_not_called()
        assert db_session.query(Job).all() == [job]

    def test_if_the_job_has_force_True_it_indexes_the_annotation_and_deletes_the_job(
        self, batch_indexer, db_session, queue, SyncAnnotationJobFactory
    ):
        job = SyncAnnotationJobFactory(force=True)

        counts = queue.sync(1)

        assert counts == {
            Queue.Result.SYNCED_FORCED: 1,
            Queue.Result.COMPLETED_FORCED: 1,
            Queue.Result.SYNCED_TOTAL: 1,
            Queue.Result.COMPLETED_TOTAL: 1,
        }
        assert db_session.query(Job).all() == []
        batch_indexer.index.assert_called_once_with([self.url_safe_id(job)])

    def test_if_the_annotation_isnt_in_the_DB_it_deletes_the_job_from_the_queue(
        self, db_session, factories, queue, SyncAnnotationJobFactory
    ):
        # We have to actually create an annotation and save it to the DB in
        # order to get a valid annotation ID. Then we delete the annotation
        # from the DB again because we actually don't want the annotation to be
        # in the DB in this test.
        annotation = factories.Annotation()
        SyncAnnotationJobFactory(annotation=annotation)
        db_session.delete(annotation)

        counts = queue.sync(1)

        assert counts == {
            Queue.Result.COMPLETED_DELETED: 1,
            Queue.Result.COMPLETED_TOTAL: 1,
        }
        assert db_session.query(Job).all() == []

    def test_if_the_annotation_is_marked_as_deleted_in_the_DB_it_deletes_the_job_from_the_queue(
        self, db_session, factories, queue, SyncAnnotationJobFactory
    ):
        annotation = factories.Annotation()
        SyncAnnotationJobFactory(annotation=annotation)
        annotation.deleted = True

        counts = queue.sync(1)

        assert counts == {
            Queue.Result.COMPLETED_DELETED: 1,
            Queue.Result.COMPLETED_TOTAL: 1,
        }
        assert db_session.query(Job).all() == []

    def test_if_the_annotation_is_missing_from_Elastic_it_indexes_it(
        self, batch_indexer, queue, SyncAnnotationJobFactory
    ):
        job = SyncAnnotationJobFactory()

        counts = queue.sync(1)

        assert counts == {
            Queue.Result.SYNCED_MISSING: 1,
            Queue.Result.SYNCED_TOTAL: 1,
        }
        batch_indexer.index.assert_called_once_with([self.url_safe_id(job)])

    def test_if_the_annotation_is_already_in_Elastic_it_removes_the_job_from_the_queue(
        self, batch_indexer, db_session, queue, SyncAnnotationJobFactory
    ):
        SyncAnnotationJobFactory(index=True)

        counts = queue.sync(1)

        assert counts == {
            Queue.Result.COMPLETED_UP_TO_DATE: 1,
            Queue.Result.COMPLETED_TOTAL: 1,
        }
        assert db_session.query(Job).all() == []
        batch_indexer.index.assert_not_called()

    def test_if_the_annotation_has_a_different_updated_time_in_Elastic_it_indexes_it(
        self, batch_indexer, factories, now, queue, SyncAnnotationJobFactory
    ):
        annotation = factories.Annotation()
        SyncAnnotationJobFactory(annotation=annotation, index=True)
        # Simulate the annotation having been updated in the DB after it was
        # indexed.
        annotation.updated = now

        counts = queue.sync(1)

        assert counts == {
            Queue.Result.SYNCED_DIFFERENT: 1,
            Queue.Result.SYNCED_TOTAL: 1,
        }
        batch_indexer.index.assert_called_once_with([annotation.id])

    def test_if_the_annotation_has_a_different_userid_in_Elastic_it_indexes_it(
        self, batch_indexer, factories, queue, SyncAnnotationJobFactory
    ):
        annotation = factories.Annotation()
        SyncAnnotationJobFactory(annotation=annotation, index=True)
        # Simulate the user having been renamed in the DB.
        annotation.userid = "new_userid"

        counts = queue.sync(1)

        assert counts == {
            Queue.Result.SYNCED_DIFFERENT: 1,
            Queue.Result.SYNCED_TOTAL: 1,
        }
        batch_indexer.index.assert_called_once_with([annotation.id])

    def test_if_there_are_multiple_jobs_with_the_same_annotation_id(
        self, batch_indexer, factories, queue, SyncAnnotationJobFactory
    ):
        annotation = factories.Annotation()
        jobs = SyncAnnotationJobFactory.create_batch(size=2, annotation=annotation)

        counts = queue.sync(len(jobs))

        # Unfortunately the method gets the metrics wrong here: it reports that
        # it synced two annotations because it processed two different jobs.
        # But actually the two jobs were for the same annotation and it only
        # synced one.
        assert counts == {
            Queue.Result.SYNCED_MISSING: 2,
            Queue.Result.SYNCED_TOTAL: 2,
        }
        # It only syncs the annotation to Elasticsearch once, even though it
        # processed two separate jobs (for the same annotation).
        batch_indexer.index.assert_called_once_with([annotation.id])

    def test_deleting_multiple_jobs_with_the_same_annotation_id(
        self, batch_indexer, db_session, factories, queue, SyncAnnotationJobFactory
    ):
        annotation = factories.Annotation()
        jobs = SyncAnnotationJobFactory.create_batch(
            size=2, annotation=annotation, index=True
        )

        counts = queue.sync(len(jobs))

        assert counts == {
            Queue.Result.COMPLETED_UP_TO_DATE: 2,
            Queue.Result.COMPLETED_TOTAL: 2,
        }
        assert db_session.query(Job).all() == []
        batch_indexer.index.assert_not_called()

    def url_safe_id(self, job):
        """Return the URL-safe version of the given job's annotation ID."""
        return URLSafeUUID.hex_to_url_safe(job.kwargs["annotation_id"])

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
    def index(self, es_client, search_index):
        """A method that indexes the given annotation into Elasticsearch."""

        def index(annotation):
            search_index.add_annotation(annotation)
            es_client.conn.indices.refresh(index=es_client.index)

        return index

    @pytest.fixture
    def SyncAnnotationJobFactory(self, factories, index, now):
        """
        A factory for creating sync_annotation jobs.

        By default this creates jobs with job.name="sync_annotation", with a
        scheduled_at time in the past, and with a job.kwargs that contains an
        annotation_id and force=False.

        By default a new annotation will be created for the job to use.

        By default the annotation will exist in the DB but will *not* be in
        Elasticsearch.

        Usage:

            SyncAnnotationJobFactory()

            # Create multiple jobs, each with its own annotation.
            SyncAnnotationJobFactory.create_batch(size=3)

            # Create a job that isn't scheduled yet.
            one_hour_from_now = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            SyncAnnotationJobFactory(scheduled_at=one_hour_from_now)

            # Create an expired job.
            one_hour_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
            SyncAnnotationJobFactory(expires_at=one_hour_ago)

            # Create multiple jobs with force=True in their kwargs.
            SyncAnnotationJobFactory.create_batch(size=3, force=True)

            # Create a job for a given annotation, instead of
            # SyncAnnotationJobFactory creating a new annotation automatically.
            annotation = factories.Annotation()
            SyncAnnotationJobFactory(annotation=annotation)

            # Create a job for an annotation that *is* already in Elasticsearch.
            SyncAnnotationJobFactory(index=True)
        """

        class SyncAnnotationJobFactory(factories.Job):
            class Meta:
                exclude = "force"

            annotation = factory.SubFactory(factories.Annotation)
            force = False

            scheduled_at = factory.LazyFunction(
                lambda: now - datetime_.timedelta(hours=1)
            )
            name = "sync_annotation"

            kwargs = factory.LazyAttribute(
                lambda o: {
                    "annotation_id": URLSafeUUID.url_safe_to_hex(o.annotation.id),
                    "force": o.force,
                }
            )

            @classmethod
            def _create(cls, model_class, *args, **kwargs):
                annotation = kwargs.pop("annotation")
                index_ = kwargs.pop("index", False)

                job = super()._create(model_class, *args, **kwargs)

                if index_:
                    index(annotation)

                return job

        return SyncAnnotationJobFactory

    @pytest.fixture(autouse=True)
    def noise_annotations(self, factories, index):
        # Create some noise annotations in the DB. Some of them also in
        # Elasticsearch, some not. None of these should ever be touched by the
        # sync() method in these tests.
        annotations = factories.Annotation.create_batch(size=2)
        index(annotations[0])


class TestCount:
    @pytest.mark.parametrize(
        "tags,expired,expected_result",
        [
            (None, False, 3),
            (None, True, 1),
            (["storage.create_annotation", "storage.update_annotation"], False, 2),
            (["storage.create_annotation", "storage.update_annotation"], True, 1),
        ],
    )
    def test_it(
        self, db_session, factories, now, queue, tags, expired, expected_result
    ):
        one_minute = datetime_.timedelta(minutes=1)

        class JobFactory(factories.Job):
            """A factory that, by default, creates jobs that should be counted."""

            name = "sync_annotation"
            tag = factory.Iterator(
                ["storage.create_annotation", "storage.update_annotation"]
            )
            scheduled_at = now - one_minute

        JobFactory.create_batch(size=2)
        JobFactory(tag="another_tag")
        JobFactory(name="another_name")
        # A job that's expired.
        JobFactory(expires_at=now - one_minute)
        # A job that isn't scheduled yet.
        JobFactory(scheduled_at=now + one_minute)

        count = queue.count(tags=tags, expired=expired)

        assert count == expected_result


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
