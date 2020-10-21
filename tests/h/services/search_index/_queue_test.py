import datetime as datetime_
import uuid
from unittest import mock

import pytest
from h_matchers import Any

from h.db.types import URLSafeUUID
from h.models import Job
from h.search.index import BatchIndexer
from h.services.search_index import SearchIndexService
from h.services.search_index._queue import Queue

LIMIT = 2
ONE_WEEK = datetime_.timedelta(weeks=1)
ONE_WEEK_IN_SECONDS = int(ONE_WEEK.total_seconds())
MINUS_5_MIN = datetime_.timedelta(minutes=-5)
MINUS_5_MIN_IN_SECS = int(MINUS_5_MIN.total_seconds())


class TestAddSyncAnnotationJob:
    def test_it(self, db_session, factories, queue, now):
        annotation = factories.Annotation.build()

        queue.add(annotation.id, "test_tag", schedule_in=ONE_WEEK_IN_SECONDS)

        assert db_session.query(Job).all() == [
            Any.instance_of(Job).with_attrs(
                dict(
                    enqueued_at=Any.instance_of(datetime_.datetime),
                    scheduled_at=now + ONE_WEEK,
                    tag="test_tag",
                    priority=1,
                    kwargs={
                        "annotation_id": URLSafeUUID.url_safe_to_hex(annotation.id),
                        "force": False,
                    },
                )
            ),
        ]


class TestAddAnnotationsBetweenTimes:
    @pytest.mark.parametrize("force", [True, False])
    def test_it(self, annotation_ids, db_session, queue, force):
        queue.add_annotations_between_times(
            datetime_.datetime(2020, 9, 9),
            datetime_.datetime(2020, 9, 11),
            "test_tag",
            force,
        )

        assert (
            db_session.query(Job).all()
            == Any.list.containing(
                [
                    Any.instance_of(Job).with_attrs(
                        {
                            "tag": "test_tag",
                            "name": "sync_annotation",
                            "scheduled_at": Any.instance_of(datetime_.datetime),
                            "priority": 1000,
                            "kwargs": {
                                "annotation_id": str(
                                    uuid.UUID(
                                        URLSafeUUID.url_safe_to_hex(annotation_id)
                                    )
                                ),
                                "force": force,
                            },
                        }
                    )
                    for annotation_id in annotation_ids
                ]
            ).only()
        )

    @pytest.fixture
    def annotations(self, factories):
        return factories.Annotation.create_batch(
            size=2, updated=datetime_.datetime(year=2020, month=9, day=10)
        )

    @pytest.fixture(autouse=True)
    def non_matching_annotations(self, factories):
        """Annotations from outside the date range that we're reindexing."""
        factories.Annotation.create(
            updated=datetime_.datetime(year=2020, month=9, day=8)
        )
        factories.Annotation.create(
            updated=datetime_.datetime(year=2020, month=9, day=12)
        )

    @pytest.fixture
    def annotation_ids(self, annotations):
        return [annotation.id for annotation in annotations]


class TestSyncAnnotations:
    def test_it_does_nothing_if_the_queue_is_empty(self, batch_indexer, queue):
        queue.sync(LIMIT)

        batch_indexer.index.assert_not_called()

    def test_it_ignores_jobs_that_arent_scheduled_yet(
        self, annotation_ids, batch_indexer, queue
    ):
        queue.add_all(annotation_ids, tag="test_tag", schedule_in=ONE_WEEK_IN_SECONDS)

        queue.sync(LIMIT)

        batch_indexer.index.assert_not_called()

    def test_it_ignores_jobs_beyond_limit(
        self, all_annotation_ids, batch_indexer, queue
    ):
        queue.add_all(
            all_annotation_ids, tag="test_tag", schedule_in=MINUS_5_MIN_IN_SECS
        )

        queue.sync(LIMIT)

        for annotation_id in all_annotation_ids[LIMIT:]:
            assert annotation_id not in batch_indexer.index.call_args[0][0]

    def test_if_the_job_has_force_True_it_indexes_the_annotation_and_deletes_the_job(
        self, annotations, annotation_ids, batch_indexer, db_session, index, queue, LOG
    ):
        index(annotations)
        queue.add_all(
            annotation_ids,
            tag="test_tag",
            schedule_in=MINUS_5_MIN_IN_SECS,
            force=True,
        )

        queue.sync(LIMIT)

        LOG.info.assert_called_with({Queue.Result.FORCED: LIMIT})
        assert db_session.query(Job).all() == []
        batch_indexer.index.assert_called_once_with(
            Any.list.containing(annotation_ids).only()
        )

    def test_if_the_annotation_isnt_in_the_DB_it_deletes_the_job_from_the_queue(
        self, annotations, annotation_ids, db_session, queue, LOG
    ):
        for annotation in annotations:
            db_session.delete(annotation)

        queue.add_all(annotation_ids, tag="test_tag", schedule_in=MINUS_5_MIN_IN_SECS)

        queue.sync(LIMIT)

        LOG.info.assert_called_with({Queue.Result.DELETED_FROM_DB: LIMIT})
        assert db_session.query(Job).all() == []

    def test_if_the_annotation_is_marked_as_deleted_in_the_DB_it_deletes_the_job_from_the_queue(
        self, annotations, annotation_ids, db_session, queue, LOG
    ):
        for annotation in annotations:
            annotation.deleted = True

        queue.add_all(annotation_ids, tag="test_tag", schedule_in=MINUS_5_MIN_IN_SECS)

        queue.sync(LIMIT)

        LOG.info.assert_called_with({Queue.Result.DELETED_FROM_DB: LIMIT})
        assert db_session.query(Job).all() == []

    def test_if_the_annotation_is_missing_from_Elastic_it_indexes_it(
        self, annotation_ids, batch_indexer, queue, LOG
    ):
        queue.add_all(annotation_ids, tag="test_tag", schedule_in=MINUS_5_MIN_IN_SECS)

        queue.sync(LIMIT)

        LOG.info.assert_called_with({Queue.Result.MISSING: LIMIT})
        batch_indexer.index.assert_called_once_with(
            Any.list.containing(annotation_ids).only()
        )

    def test_if_the_annotation_is_already_in_Elastic_it_removes_the_job_from_the_queue(
        self,
        annotations,
        annotation_ids,
        batch_indexer,
        db_session,
        index,
        queue,
        LOG,
    ):
        index(annotations)
        queue.add_all(annotation_ids, tag="test_tag", schedule_in=MINUS_5_MIN_IN_SECS)

        queue.sync(LIMIT)

        LOG.info.assert_called_with({Queue.Result.UP_TO_DATE: LIMIT})
        assert db_session.query(Job).all() == []
        batch_indexer.index.assert_not_called()

    def test_if_the_annotation_has_a_different_updated_time_in_Elastic_it_indexes_it(
        self, annotations, annotation_ids, batch_indexer, index, now, queue, LOG
    ):
        index(annotations)
        queue.add_all(annotation_ids, tag="test_tag", schedule_in=MINUS_5_MIN_IN_SECS)
        # Simulate the annotations having been updated in the DB after they
        # were indexed.
        for annotation in annotations:
            annotation.updated = now

        queue.sync(LIMIT)

        LOG.info.assert_called_with({Queue.Result.OUT_OF_DATE: LIMIT})
        batch_indexer.index.assert_called_once_with(
            Any.list.containing(annotation_ids).only()
        )

    def test_if_there_are_multiple_jobs_with_the_same_annotation_id(
        self, annotation_ids, batch_indexer, queue, LOG
    ):
        queue.add_all(
            [annotation_ids[0] for _ in range(LIMIT)],
            tag="test_tag",
            schedule_in=MINUS_5_MIN_IN_SECS,
        )

        queue.sync(LIMIT)

        # It only syncs the annotation to Elasticsearch once.
        LOG.info.assert_called_with({Queue.Result.MISSING: LIMIT})
        batch_indexer.index.assert_called_once_with(
            Any.list.containing([annotation_ids[0]]).only()
        )

    def test_deleting_multiple_jobs_with_the_same_annotation_id(
        self, annotations, batch_indexer, db_session, index, queue, LOG
    ):
        queue.add_all(
            [annotations[0].id for _ in range(LIMIT)],
            tag="test_tag",
            schedule_in=MINUS_5_MIN_IN_SECS,
        )
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
    def index(self, es_client, search_index, nipsa_service):
        """A function for adding annotations to Elasticsearch."""

        def index(annotations):
            """Add `annotations` to the Elasticsearch index."""
            for annotation in annotations:
                search_index.add_annotation(annotation)

            es_client.conn.indices.refresh(index=es_client.index)

        return index


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
