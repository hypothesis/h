import datetime
import logging
from unittest import mock

import pytest
from h_matchers import Any

from h.models import Job
from h.search.client import Client
from h.search.index import BatchIndexer
from h.services.search_index._queue import Queue


class TestAddSyncAnnotationJob:
    def test_it(self, db_session, queue):
        queue.add("test_annotation_id", "test_tag", scheduled_at=ONE_WEEK_FROM_NOW)

        assert db_session.query(Job).all() == [
            Any.instance_of(Job).with_attrs(
                dict(
                    enqueued_at=Any.instance_of(datetime.datetime),
                    scheduled_at=ONE_WEEK_FROM_NOW,
                    tag="test_tag",
                    kwargs={"annotation_id": "test_annotation_id"},
                )
            ),
        ]

    def test_scheduled_at_defaults_to_now(self, db_session, queue):
        queue.add("test_annotation_id", "test_tag")

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
    def test_it_does_nothing_if_the_queue_is_empty(self, batch_indexer, caplog, queue):
        queue.sync()

        batch_indexer.index.assert_not_called()
        assert caplog.records == []

    def test_it_ignores_jobs_that_arent_scheduled_yet(
        self, annotation_ids, batch_indexer, caplog, queue
    ):
        queue.add_all(
            annotation_ids,
            tag="test",
            scheduled_at=ONE_WEEK_FROM_NOW,
        )

        queue.sync()

        batch_indexer.index.assert_not_called()
        assert caplog.records == []

    def test_it_ignores_jobs_beyond_limit(self, annotation_ids, batch_indexer, queue):
        queue.add_all(
            annotation_ids,
            tag="test",
        )

        queue.sync()

        for annotation_id in annotation_ids[LIMIT:]:
            assert annotation_id not in batch_indexer.index.call_args[0][0]

    def test_if_the_annotation_isnt_in_the_DB_it_deletes_the_job_from_the_queue(
        self,
        annotations,
        annotation_ids,
        caplog,
        db_session,
        queue,
    ):
        for annotation in annotations[:LIMIT]:
            db_session.delete(annotation)

        queue.add_all(
            annotation_ids[:LIMIT],
            tag="test",
            scheduled_at=FIVE_MINUTES_AGO,
        )

        queue.sync()

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
        queue,
    ):
        for annotation in annotations[:LIMIT]:
            annotation.deleted = True

        queue.add_all(
            annotation_ids[:LIMIT],
            tag="test",
            scheduled_at=FIVE_MINUTES_AGO,
        )

        queue.sync()

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
        queue,
    ):
        queue.add_all(
            annotation_ids[:LIMIT],
            tag="test",
            scheduled_at=FIVE_MINUTES_AGO,
        )

        queue.sync()

        assert caplog.record_tuples == [
            (
                Any(),
                Any(),
                "Syncing 10 annotations that are missing from Elasticsearch",
            )
        ]
        batch_indexer.index.assert_called_once_with(
            Any.list.containing(annotation_ids[:LIMIT]).only()
        )

    def test_if_the_annotation_is_already_in_Elastic_it_removes_the_job_from_the_queue(
        self,
        annotations,
        annotation_ids,
        batch_indexer,
        caplog,
        db_session,
        es,
        queue,
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
                    for annotation in annotations[:LIMIT]
                ],
            },
        }
        queue.add_all(
            annotation_ids[:LIMIT],
            tag="test",
            scheduled_at=FIVE_MINUTES_AGO,
        )

        queue.sync()

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
        queue,
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
                    for annotation in annotations[:LIMIT]
                ],
            },
        }
        queue.add_all(
            annotation_ids[:LIMIT],
            tag="test",
            scheduled_at=FIVE_MINUTES_AGO,
        )

        queue.sync()

        assert caplog.record_tuples == [
            (
                Any(),
                Any(),
                "Syncing 10 annotations that are different in Elasticsearch",
            )
        ]
        batch_indexer.index.assert_called_once_with(
            Any.list.containing(annotation_ids[:LIMIT]).only()
        )

    def test_if_there_are_multiple_jobs_with_the_same_annotation_id(
        self,
        annotation_ids,
        batch_indexer,
        caplog,
        es,
        queue,
    ):
        queue.add_all(
            [annotation_ids[0], annotation_ids[0], annotation_ids[0]],
            tag="test",
            scheduled_at=FIVE_MINUTES_AGO,
        )

        queue.sync()

        # It only retrieves the annotation from Elasticsearch once.
        es.conn.search.assert_called_once_with(
            body=Any.dict.containing(
                {
                    "query": Any.dict.containing(
                        {
                            "ids": {
                                "values": [annotation_ids[0]],
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
            Any.list.containing([annotation_ids[0]]).only()
        )

    def test_deleting_multiple_jobs_with_the_same_annotation_id(
        self,
        annotations,
        batch_indexer,
        caplog,
        db_session,
        es,
        queue,
    ):
        queue.add_all(
            [annotations[0].id, annotations[0].id, annotations[0].id],
            tag="test",
            scheduled_at=FIVE_MINUTES_AGO,
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

        queue.sync()

        assert caplog.record_tuples == [
            (
                Any(),
                Any(),
                "Deleting 3 successfully completed jobs from the queue",
            )
        ]
        assert db_session.query(Job).all() == []
        batch_indexer.index.assert_not_called()


ONE_WEEK_FROM_NOW = datetime.datetime.utcnow() + datetime.timedelta(weeks=1)


FIVE_MINUTES_AGO = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)


LIMIT = 10


@pytest.fixture
def annotations(factories):
    return factories.Annotation.create_batch(size=20)


@pytest.fixture
def annotation_ids(annotations):
    return [annotation.id for annotation in annotations]


@pytest.fixture
def batch_indexer():
    return mock.create_autospec(BatchIndexer, spec_set=True, instance=True)


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
def queue(batch_indexer, db_session, es):
    return Queue(db_session, es, batch_indexer, LIMIT)
