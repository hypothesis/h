import datetime as datetime_
import logging
from unittest import mock

import pytest
from h_matchers import Any

from h.models import Job
from h.presenters import AnnotationSearchIndexPresenter
from h.search.index import BatchIndexer
from h.services.search_index._queue import Queue


class TestAddSyncAnnotationJob:
    def test_it(self, db_session, queue, now):
        queue.add("test_annotation_id", "test_tag", scheduled_at=ONE_WEEK)

        assert db_session.query(Job).all() == [
            Any.instance_of(Job).with_attrs(
                dict(
                    enqueued_at=Any.instance_of(datetime_.datetime),
                    scheduled_at=now + ONE_WEEK,
                    tag="test_tag",
                    kwargs={"annotation_id": "test_annotation_id"},
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
        queue.add_all(annotation_ids, tag="test", scheduled_at=ONE_WEEK)

        queue.sync()

        batch_indexer.index.assert_not_called()
        assert caplog.records == []

    def test_it_ignores_jobs_beyond_limit(self, annotation_ids, batch_indexer, queue):
        queue.add_all(annotation_ids, tag="test", scheduled_at=MINUS_FIVE_MINUTES)

        queue.sync()

        for annotation_id in annotation_ids[LIMIT:]:
            assert annotation_id not in batch_indexer.index.call_args[0][0]

    def test_if_the_annotation_isnt_in_the_DB_it_deletes_the_job_from_the_queue(
        self, annotations, annotation_ids, caplog, db_session, queue
    ):
        for annotation in annotations[:LIMIT]:
            db_session.delete(annotation)

        queue.add_all(
            annotation_ids[:LIMIT], tag="test", scheduled_at=MINUS_FIVE_MINUTES
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
        self, annotations, annotation_ids, caplog, db_session, queue
    ):
        for annotation in annotations[:LIMIT]:
            annotation.deleted = True

        queue.add_all(
            annotation_ids[:LIMIT], tag="test", scheduled_at=MINUS_FIVE_MINUTES
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
        self, annotation_ids, batch_indexer, caplog, queue
    ):
        queue.add_all(
            annotation_ids[:LIMIT], tag="test", scheduled_at=MINUS_FIVE_MINUTES
        )

        queue.sync()

        assert caplog.record_tuples == [
            (Any(), Any(), "Syncing 10 annotations that are missing from Elasticsearch")
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
        index,
        queue,
    ):
        index(annotations[:LIMIT])
        queue.add_all(
            annotation_ids[:LIMIT], tag="test", scheduled_at=MINUS_FIVE_MINUTES
        )

        queue.sync()

        assert caplog.record_tuples == [
            (Any(), Any(), "Deleting 10 successfully completed jobs from the queue")
        ]
        assert db_session.query(Job).all() == []
        batch_indexer.index.assert_not_called()

    def test_if_the_annotation_has_a_different_updated_time_in_Elastic_it_indexes_it(
        self, annotations, annotation_ids, batch_indexer, caplog, index, now, queue
    ):
        index(annotations[:LIMIT], updated=now - datetime_.timedelta(minutes=5))
        queue.add_all(
            annotation_ids[:LIMIT], tag="test", scheduled_at=MINUS_FIVE_MINUTES
        )

        queue.sync()

        assert caplog.record_tuples == [
            (Any(), Any(), "Syncing 10 annotations that are different in Elasticsearch")
        ]
        batch_indexer.index.assert_called_once_with(
            Any.list.containing(annotation_ids[:LIMIT]).only()
        )

    def test_if_there_are_multiple_jobs_with_the_same_annotation_id(
        self, annotation_ids, batch_indexer, caplog, queue
    ):
        queue.add_all(
            [annotation_ids[0], annotation_ids[0], annotation_ids[0]],
            tag="test",
            scheduled_at=MINUS_FIVE_MINUTES,
        )

        queue.sync()

        # It only syncs the annotation to Elasticsearch once.
        assert caplog.record_tuples == [
            (Any(), Any(), "Syncing 1 annotations that are missing from Elasticsearch")
        ]
        batch_indexer.index.assert_called_once_with(
            Any.list.containing([annotation_ids[0]]).only()
        )

    def test_deleting_multiple_jobs_with_the_same_annotation_id(
        self, annotations, batch_indexer, caplog, db_session, index, queue
    ):
        queue.add_all(
            [annotations[0].id, annotations[0].id, annotations[0].id],
            tag="test",
            scheduled_at=MINUS_FIVE_MINUTES,
        )
        index([annotations[0]])

        queue.sync()

        assert caplog.record_tuples == [
            (Any(), Any(), "Deleting 3 successfully completed jobs from the queue")
        ]
        assert db_session.query(Job).all() == []
        batch_indexer.index.assert_not_called()


ONE_WEEK = datetime_.timedelta(weeks=1)


MINUS_FIVE_MINUTES = datetime_.timedelta(minutes=-5)


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
    caplog.set_level(logging.CRITICAL, "elasticsearch")
    caplog.set_level(logging.INFO)
    return caplog


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
    return Queue(db_session, es_client, batch_indexer, LIMIT)


@pytest.fixture
def index(es_client, moderation_service, nipsa_service, pyramid_request):
    """A function for adding annotations to Elasticsearch."""

    def index(annotations, updated=None):
        """Add `annotations` to the Elasticsearch index."""
        for annotation in annotations:
            body = AnnotationSearchIndexPresenter(annotation, pyramid_request).asdict()

            if updated is not None:
                body["updated"] = updated

            es_client.conn.index(
                index=es_client.index,
                doc_type=es_client.mapping_type,
                body=body,
                id=annotation.id,
            )
        es_client.conn.indices.refresh(index=es_client.index)

    return index
