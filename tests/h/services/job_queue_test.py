import datetime
import logging
from unittest import mock

import pytest
from h_matchers import Any

from h.models import Job
from h.search.client import Client
from h.services.job_queue import JobQueue, factory


class TestAddSyncAnnotationJob:
    def test_it(self, db_session, job_queue):
        job_queue.add_sync_annotation_job(
            "test_annotation_id", "test_tag", scheduled_at=one_week_from_now
        )

        assert db_session.query(Job).all() == [
            Any.instance_of(Job).with_attrs(
                dict(
                    enqueued_at=Any.instance_of(datetime.datetime),
                    scheduled_at=one_week_from_now,
                    tag="test_tag",
                    kwargs={"annotation_id": "test_annotation_id"},
                )
            ),
        ]

    def test_scheduled_at_defaults_to_now(self, db_session, job_queue):
        job_queue.add_sync_annotation_job("test_annotation_id", "test_tag")

        assert db_session.query(Job).all() == [
            Any.instance_of(Job).with_attrs(
                dict(
                    enqueued_at=Any(),
                    scheduled_at=Any.instance_of(datetime.datetime),
                    tag=Any(),
                    kwargs=Any(),
                )
            ),
        ]


class TestSyncAnnotations:
    def test_it_does_nothing_if_the_queue_is_empty(
        self, batch_indexer, caplog, job_queue
    ):
        job_queue.sync_annotations()

        batch_indexer.index.assert_not_called()
        assert caplog.records == []

    def test_it_ignores_jobs_that_arent_scheduled_yet(
        self, annotation_ids, batch_indexer, caplog, job_queue
    ):
        job_queue.add_sync_annotation_jobs(
            annotation_ids,
            tag="test",
            scheduled_at=one_week_from_now,
        )

        job_queue.sync_annotations()

        batch_indexer.index.assert_not_called()
        assert caplog.records == []

    def test_it_ignores_jobs_beyond_limit(
        self, annotation_ids, batch_indexer, job_queue
    ):
        job_queue.add_sync_annotation_jobs(
            annotation_ids,
            tag="test",
        )

        job_queue.sync_annotations()

        for annotation_id in annotation_ids[limit:]:
            assert annotation_id not in batch_indexer.index.call_args[0][0]

    def test_if_the_annotation_isnt_in_the_DB_it_deletes_the_job_from_the_queue(
        self,
        annotations,
        annotation_ids,
        caplog,
        db_session,
        job_queue,
    ):
        for annotation in annotations[:limit]:
            db_session.delete(annotation)

        job_queue.add_sync_annotation_jobs(
            annotation_ids[:limit],
            tag="test",
            scheduled_at=five_minutes_ago,
        )

        job_queue.sync_annotations()

        assert caplog.record_tuples == [
            (
                Any(),
                Any(),
                "Deleting 10 sync annotation jobs because their annotations have been deleted from the DB",
            )
        ]
        assert db_session.query(Job).all() == []

    def test_if_the_annotation_is_marked_as_deleted_in_the_DB_it_deletes_the_job_from_the_queue(
        self,
        annotations,
        annotation_ids,
        caplog,
        db_session,
        job_queue,
    ):
        for annotation in annotations[:limit]:
            annotation.deleted = True

        job_queue.add_sync_annotation_jobs(
            annotation_ids[:limit],
            tag="test",
            scheduled_at=five_minutes_ago,
        )

        job_queue.sync_annotations()

        assert caplog.record_tuples == [
            (
                Any(),
                Any(),
                "Deleting 10 sync annotation jobs because their annotations have been deleted from the DB",
            )
        ]
        assert db_session.query(Job).all() == []

    def test_if_the_annotation_is_missing_from_Elastic_it_indexes_it(
        self,
        annotation_ids,
        batch_indexer,
        caplog,
        job_queue,
    ):
        job_queue.add_sync_annotation_jobs(
            annotation_ids[:limit],
            tag="test",
            scheduled_at=five_minutes_ago,
        )

        job_queue.sync_annotations()

        assert caplog.record_tuples == [
            (
                Any(),
                Any(),
                "Syncing 10 annotations that are missing from Elasticsearch",
            )
        ]
        batch_indexer.index.assert_called_once_with(
            Any.iterable.containing(annotation_ids[:limit]).only()
        )

    def test_if_the_annotation_is_already_in_Elastic_it_removes_the_job_from_the_queue(
        self,
        annotations,
        annotation_ids,
        batch_indexer,
        caplog,
        db_session,
        es,
        job_queue,
    ):
        es.conn.search.return_value = {
            "hits": {
                "hits": [
                    {
                        "_id": annotation.id,
                        "_source": {
                            "updated": (annotation.updated).isoformat(),
                        },
                    }
                    for annotation in annotations[:limit]
                ],
            },
        }
        job_queue.add_sync_annotation_jobs(
            annotation_ids[:limit],
            tag="test",
            scheduled_at=five_minutes_ago,
        )

        job_queue.sync_annotations()

        assert caplog.record_tuples == [
            (
                Any(),
                Any(),
                "Deleting 10 successfully completed jobs from the queue",
            )
        ]
        assert db_session.query(Job).all() == []
        batch_indexer.index.assert_not_called()

    def test_if_the_annotation_has_a_different_updated_time_in_Elastic_it_indexes_it(
        self,
        annotations,
        annotation_ids,
        batch_indexer,
        caplog,
        es,
        job_queue,
    ):
        es.conn.search.return_value = {
            "hits": {
                "hits": [
                    {
                        "_id": annotation.id,
                        "_source": {
                            "updated": (
                                annotation.updated - datetime.timedelta(minutes=5)
                            ).isoformat(),
                        },
                    }
                    for annotation in annotations[:limit]
                ],
            },
        }
        job_queue.add_sync_annotation_jobs(
            annotation_ids[:limit],
            tag="test",
            scheduled_at=five_minutes_ago,
        )

        job_queue.sync_annotations()

        assert caplog.record_tuples == [
            (
                Any(),
                Any(),
                "Syncing 10 annotations that are different in Elasticsearch",
            )
        ]
        batch_indexer.index.assert_called_once_with(
            Any.iterable.containing(annotation_ids[:limit]).only()
        )

    def test_if_there_are_multiple_jobs_with_the_same_annotation_id(
        self,
        annotation_ids,
        batch_indexer,
        caplog,
        es,
        job_queue,
    ):
        job_queue.add_sync_annotation_jobs(
            [annotation_ids[0], annotation_ids[0], annotation_ids[0]],
            tag="test",
            scheduled_at=five_minutes_ago,
        )

        job_queue.sync_annotations()

        # It only retrieves the annotation from Elasticsearch once.
        es.conn.search.assert_called_once_with(
            body=Any.dict.containing(
                {
                    "query": Any.dict.containing(
                        {
                            "ids": {
                                "values": {annotation_ids[0]},
                            },
                        },
                    ),
                },
            ),
        )

        # It only syncs the annotation to Elasticsearch once.
        assert caplog.record_tuples == [
            (
                Any(),
                Any(),
                "Syncing 1 annotations that are missing from Elasticsearch",
            )
        ]
        batch_indexer.index.assert_called_once_with(
            Any.iterable.containing([annotation_ids[0]]).only()
        )

    def test_deleting_multiple_jobs_with_the_same_annotation_id(
        self,
        annotations,
        batch_indexer,
        caplog,
        db_session,
        es,
        job_queue,
    ):
        job_queue.add_sync_annotation_jobs(
            [annotations[0].id, annotations[0].id, annotations[0].id],
            tag="test",
            scheduled_at=five_minutes_ago,
        )
        es.conn.search.return_value = {
            "hits": {
                "hits": [
                    {
                        "_id": annotations[0].id,
                        "_source": {
                            "updated": (annotations[0].updated).isoformat(),
                        },
                    }
                ],
            },
        }

        job_queue.sync_annotations()

        assert caplog.record_tuples == [
            (
                Any(),
                Any(),
                "Deleting 3 successfully completed jobs from the queue",
            )
        ]
        assert db_session.query(Job).all() == []
        batch_indexer.index.assert_not_called()


class TestFactory:
    def test_it(self, pyramid_request, BatchIndexer, JobQueue):
        pyramid_request.registry.settings["h.es_sync_job_limit"] = 10
        pyramid_request.es = mock.sentinel.es

        job_queue = factory(mock.sentinel.context, pyramid_request)

        BatchIndexer.assert_called_once_with(
            pyramid_request.db, pyramid_request.es, pyramid_request
        )
        JobQueue.assert_called_once_with(
            pyramid_request.db,
            pyramid_request.es,
            BatchIndexer.return_value,
            10,
        )
        assert job_queue == JobQueue.return_value

    @pytest.fixture
    def JobQueue(self, patch):
        return patch("h.services.job_queue.JobQueue")


one_week_from_now = datetime.datetime.utcnow() + datetime.timedelta(weeks=1)


five_minutes_ago = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)


limit = 10


@pytest.fixture
def annotations(factories):
    return factories.Annotation.create_batch(size=20)


@pytest.fixture
def annotation_ids(annotations):
    return [annotation.id for annotation in annotations]


@pytest.fixture
def BatchIndexer(patch):
    return patch("h.services.job_queue.BatchIndexer")


@pytest.fixture
def batch_indexer(BatchIndexer):
    return BatchIndexer.return_value


@pytest.fixture
def caplog(caplog):
    caplog.set_level(logging.INFO)
    return caplog


@pytest.fixture
def es():
    es = mock.create_autospec(Client, spec_set=True, instance=True)
    es.conn.search.return_value = {"hits": {"hits": []}}
    return es


@pytest.fixture
def job_queue(batch_indexer, db_session, es):
    return JobQueue(db_session, es, batch_indexer, limit)
