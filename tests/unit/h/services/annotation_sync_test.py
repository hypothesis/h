import datetime
from unittest.mock import create_autospec, sentinel

import pytest
from h_matchers import Any

from h.db.types import URLSafeUUID
from h.search.index import BatchIndexer
from h.services.annotation_sync import (
    AnnotationSyncService,
    Counter,
    DBHelper,
    ESHelper,
    factory,
)
from h.services.search_index import SearchIndexService

pytestmark = [
    pytest.mark.xdist_group("elasticsearch"),
    pytest.mark.usefixtures("init_elasticsearch"),
]


class TestAnnotationSyncService:
    def test_it_does_nothing_if_the_queue_is_empty(
        self, batch_indexer, svc, queue_service
    ):
        queue_service.get.return_value = []
        counts = svc.sync(1)

        assert counts == {}
        batch_indexer.index.assert_not_called()

    def test_if_the_job_has_force_True_it_indexes_the_annotation_and_deletes_the_job(
        self, batch_indexer, factories, svc, queue_service
    ):
        job = factories.SyncAnnotationJob(force=True)
        queue_service.get.return_value = [job]

        counts = svc.sync(1)

        assert counts == {
            Counter.Result.SYNCED_FORCED.format(tag="test_tag"): 1,
            Counter.Result.SYNCED_TAG_TOTAL.format(tag="test_tag"): 1,
            Counter.Result.SYNCED_TOTAL: 1,
            Counter.Result.COMPLETED_FORCED.format(tag="test_tag"): 1,
            Counter.Result.COMPLETED_TAG_TOTAL.format(tag="test_tag"): 1,
            Counter.Result.COMPLETED_TOTAL: 1,
        }
        queue_service.delete.assert_called_once_with([job])
        batch_indexer.index.assert_called_once_with([url_safe_annotation_id(job)])

    def test_if_the_annotation_is_marked_as_deleted_in_the_DB_then_it_deletes_it_from_Elastic(
        self, factories, svc, queue_service, index
    ):
        annotation = factories.Annotation()
        index(annotation)
        job = factories.SyncAnnotationJob(annotation=annotation)
        queue_service.get.return_value = [job]
        annotation.deleted = True

        counts = svc.sync(1)

        assert counts == {
            Counter.Result.SYNCED_DELETED.format(tag="test_tag"): 1,
            Counter.Result.SYNCED_TAG_TOTAL.format(tag="test_tag"): 1,
            Counter.Result.SYNCED_TOTAL: 1,
        }
        queue_service.delete.assert_called_once_with([])

    def test_if_the_annotation_isnt_in_the_DB_then_it_deletes_it_from_Elastic(
        self, factories, svc, queue_service, index, db_session
    ):
        # We have to actually create an annotation and save it to the DB in
        # order to get a valid annotation ID. Then we delete the annotation
        # from the DB again because we actually don't want the annotation to be
        # in the DB in this test.
        annotation = factories.Annotation()
        index(annotation)
        job = factories.SyncAnnotationJob(annotation=annotation)
        queue_service.get.return_value = [job]
        db_session.delete(annotation)
        db_session.commit()

        counts = svc.sync(1)

        assert counts == {
            Counter.Result.SYNCED_DELETED.format(tag="test_tag"): 1,
            Counter.Result.SYNCED_TAG_TOTAL.format(tag="test_tag"): 1,
            Counter.Result.SYNCED_TOTAL: 1,
        }
        queue_service.delete.assert_called_once_with([])

    def test_if_the_annotation_is_marked_as_deleted_in_the_DB_and_Elastic_it_deletes_the_job_from_the_queue(
        self, factories, svc, queue_service, delete_from_elasticsearch
    ):
        annotation = factories.Annotation(deleted=True)
        annotation.deleted = True
        delete_from_elasticsearch(annotation)
        job = factories.SyncAnnotationJob(annotation=annotation)
        queue_service.get.return_value = [job]

        counts = svc.sync(1)

        assert counts == {
            Counter.Result.COMPLETED_DELETED.format(tag="test_tag"): 1,
            Counter.Result.COMPLETED_TAG_TOTAL.format(tag="test_tag"): 1,
            Counter.Result.COMPLETED_TOTAL: 1,
        }
        queue_service.delete.assert_called_once_with([job])

    def test_if_the_annotation_isnt_in_the_DB_or_Elastic_it_deletes_the_job_from_the_queue(
        self, db_session, factories, svc, queue_service
    ):
        # We have to actually create an annotation and save it to the DB in
        # order to get a valid annotation ID. Then we delete the annotation
        # from the DB again because we actually don't want the annotation to be
        # in the DB in this test.
        annotation = factories.Annotation()
        job = factories.SyncAnnotationJob(annotation=annotation)
        queue_service.get.return_value = [job]
        db_session.delete(annotation)
        db_session.commit()

        counts = svc.sync(1)

        assert counts == {
            Counter.Result.COMPLETED_DELETED.format(tag="test_tag"): 1,
            Counter.Result.COMPLETED_TAG_TOTAL.format(tag="test_tag"): 1,
            Counter.Result.COMPLETED_TOTAL: 1,
        }
        queue_service.delete.assert_called_once_with([job])

    def test_if_the_annotation_is_marked_as_deleted_in_the_DB_it_deletes_the_job_from_the_queue(
        self, factories, svc, queue_service
    ):
        annotation = factories.Annotation()
        job = factories.SyncAnnotationJob(annotation=annotation)
        queue_service.get.return_value = [job]
        annotation.deleted = True

        counts = svc.sync(1)

        assert counts == {
            Counter.Result.COMPLETED_DELETED.format(tag="test_tag"): 1,
            Counter.Result.COMPLETED_TAG_TOTAL.format(tag="test_tag"): 1,
            Counter.Result.COMPLETED_TOTAL: 1,
        }
        queue_service.delete.assert_called_once_with([job])

    def test_if_the_annotation_is_missing_from_Elastic_it_indexes_it(
        self, batch_indexer, factories, svc, queue_service
    ):
        job = factories.SyncAnnotationJob()
        queue_service.get.return_value = [job]

        counts = svc.sync(1)

        assert counts == {
            Counter.Result.SYNCED_MISSING.format(tag="test_tag"): 1,
            Counter.Result.SYNCED_TAG_TOTAL.format(tag="test_tag"): 1,
            Counter.Result.SYNCED_TOTAL: 1,
        }
        batch_indexer.index.assert_called_once_with([url_safe_annotation_id(job)])

    def test_if_the_annotation_is_already_in_Elastic_it_removes_the_job_from_the_queue(
        self, batch_indexer, factories, index, svc, queue_service
    ):
        annotation = factories.Annotation()
        index(annotation)
        job = factories.SyncAnnotationJob(annotation=annotation)
        queue_service.get.return_value = [job]

        counts = svc.sync(1)

        assert counts == {
            Counter.Result.COMPLETED_UP_TO_DATE.format(tag="test_tag"): 1,
            Counter.Result.COMPLETED_TAG_TOTAL.format(tag="test_tag"): 1,
            Counter.Result.COMPLETED_TOTAL: 1,
        }
        queue_service.delete.assert_called_once_with([job])
        batch_indexer.index.assert_not_called()

    def test_if_the_annotation_has_a_different_updated_time_in_Elastic_it_indexes_it(
        self, batch_indexer, factories, index, now, svc, queue_service
    ):
        annotation = factories.Annotation()
        index(annotation)
        job = factories.SyncAnnotationJob(annotation=annotation)
        queue_service.get.return_value = [job]
        # Simulate the annotation having been updated in the DB after it was
        # indexed.
        annotation.updated = now

        counts = svc.sync(1)

        assert counts == {
            Counter.Result.SYNCED_DIFFERENT.format(tag="test_tag"): 1,
            Counter.Result.SYNCED_TAG_TOTAL.format(tag="test_tag"): 1,
            Counter.Result.SYNCED_TOTAL: 1,
        }
        batch_indexer.index.assert_called_once_with([annotation.id])

    def test_if_the_annotation_has_a_different_userid_in_Elastic_it_indexes_it(
        self, batch_indexer, factories, index, svc, queue_service
    ):
        annotation = factories.Annotation()
        index(annotation)
        job = factories.SyncAnnotationJob(annotation=annotation)
        queue_service.get.return_value = [job]
        # Simulate the user having been renamed in the DB.
        annotation.userid = "new_userid"

        counts = svc.sync(1)

        assert counts == {
            Counter.Result.SYNCED_DIFFERENT.format(tag="test_tag"): 1,
            Counter.Result.SYNCED_TAG_TOTAL.format(tag="test_tag"): 1,
            Counter.Result.SYNCED_TOTAL: 1,
        }
        batch_indexer.index.assert_called_once_with([annotation.id])

    def test_if_there_are_multiple_jobs_with_the_same_annotation_id(
        self, batch_indexer, factories, svc, queue_service
    ):
        annotation = factories.Annotation()
        jobs = factories.SyncAnnotationJob.create_batch(size=2, annotation=annotation)
        queue_service.get.return_value = jobs

        counts = svc.sync(len(jobs))

        assert counts == {
            Counter.Result.SYNCED_MISSING.format(tag="test_tag"): 1,
            Counter.Result.SYNCED_TAG_TOTAL.format(tag="test_tag"): 1,
            Counter.Result.SYNCED_TOTAL: 1,
        }
        # It only syncs the annotation to Elasticsearch once, even though it
        # processed two separate jobs (for the same annotation).
        batch_indexer.index.assert_called_once_with([annotation.id])

    def test_deleting_multiple_jobs_with_the_same_annotation_id(
        self, batch_indexer, factories, index, svc, queue_service
    ):
        annotation = factories.Annotation()
        index(annotation)
        jobs = factories.SyncAnnotationJob.create_batch(size=2, annotation=annotation)
        queue_service.get.return_value = jobs

        counts = svc.sync(len(jobs))

        assert counts == {
            Counter.Result.COMPLETED_UP_TO_DATE.format(tag="test_tag"): 2,
            Counter.Result.COMPLETED_TAG_TOTAL.format(tag="test_tag"): 2,
            Counter.Result.COMPLETED_TOTAL: 2,
        }
        queue_service.delete.assert_called_once_with(Any.list.containing(jobs).only())
        batch_indexer.index.assert_not_called()

    def test_metrics(self, factories, index, now, svc, queue_service):
        queue_service.get.return_value = []

        def add_job(indexed=True, updated=False, deleted=False, **kwargs):
            annotation = factories.Annotation()
            job = factories.SyncAnnotationJob(annotation=annotation, **kwargs)
            queue_service.get.return_value.append(job)

            if indexed:
                index(annotation)

            if updated:
                annotation.updated = now + datetime.timedelta(weeks=1)

            if deleted:
                annotation.deleted = True

        add_job()
        add_job(indexed=False)
        add_job(updated=True)
        add_job(deleted=True)
        add_job(tag="tag_2", force=True)

        counts = svc.sync(5)

        assert counts == {
            "Synced/Total": 4,
            "Completed/Total": 2,
            "Synced/test_tag/Total": 3,
            "Completed/test_tag/Total": 1,
            "Synced/test_tag/Deleted_from_db": 1,
            "Synced/test_tag/Different_in_Elastic": 1,
            "Synced/test_tag/Missing_from_Elastic": 1,
            "Synced/tag_2/Forced": 1,
            "Synced/tag_2/Total": 1,
            "Completed/tag_2/Forced": 1,
            "Completed/tag_2/Total": 1,
            "Completed/test_tag/Up_to_date_in_Elastic": 1,
        }

    @pytest.fixture
    def now(self):
        """Return the current UTC time."""
        return datetime.datetime.utcnow()

    @pytest.fixture(autouse=True)
    def noise_annotations(self, factories, index):
        """
        Create some noise annotations in the DB.

        Also add some of the noise annotations to Elasticsearch, some not.

        None of these noise annotations should ever be touched by the sync()
        method in these tests.
        """
        annotations = factories.Annotation.create_batch(size=2)
        index(annotations[0])

    @pytest.fixture
    def batch_indexer(self):
        """Return a mock BatchIndexer instance."""
        return create_autospec(BatchIndexer, spec_set=True, instance=True)

    @pytest.fixture
    def svc(self, batch_indexer, db_session, es_client, queue_service):
        return AnnotationSyncService(
            batch_indexer=batch_indexer,
            db_helper=DBHelper(db=db_session),
            es_helper=ESHelper(es=es_client),
            queue_service=queue_service,
        )


class TestDBHelper:
    def test_get_with_no_jobs(self, db_helper):
        assert db_helper.get([]) == {}

    def test_get_when_all_jobs_have_force_True(self, db_helper, db_session, factories):
        jobs = factories.SyncAnnotationJob.create_batch(2, force=True)
        # Flush the DB to generate job.id values.
        db_session.flush()

        assert db_helper.get(jobs) == {}

    def test_get_filters_out_duplicate_annotations(
        self, db_helper, db_session, factories
    ):
        annotation = factories.Annotation()
        # Two jobs for the same annotation.
        jobs = factories.SyncAnnotationJob.create_batch(2, annotation=annotation)
        # Flush the DB to generate job.id values.
        db_session.flush()

        result = db_helper.get(jobs)

        assert list(result.keys()) == [annotation.id]

    def test_get(self, db_helper, db_session, factories):
        annotations = factories.Annotation.create_batch(2)
        jobs = [
            factories.SyncAnnotationJob(annotation=annotation)
            for annotation in annotations
        ]
        # A duplicate job for one of the same annotations. This should be ignored.
        jobs.append(factories.SyncAnnotationJob(annotation=annotations[0]))
        # A job whose annotation is marked as deleted. This should be ignored.
        jobs.append(
            factories.SyncAnnotationJob(annotation=factories.Annotation(deleted=True))
        )
        # A job that has force=True. This should be ignored.
        jobs.append(factories.SyncAnnotationJob(force=True))
        # An annotation that has no job. This should be ignored.
        factories.Annotation()
        # Flush the DB to generate job.id values.
        db_session.flush()

        result = db_helper.get(jobs)

        assert result == {
            annotations[0].id: (
                annotations[0].id,
                annotations[0].updated,
                annotations[0].userid,
            ),
            annotations[1].id: (
                annotations[1].id,
                annotations[1].updated,
                annotations[1].userid,
            ),
        }

    # TODO: Annotations that don't exist in the DB.

    @pytest.fixture
    def db_helper(self, db_session):
        return DBHelper(db_session)


class TestESHelper:
    def test_get_with_no_jobs(self, es_helper):
        assert es_helper.get([]) == {}

    def test_get_when_all_jobs_have_force_True(self, db_session, es_helper, factories):
        jobs = factories.SyncAnnotationJob.create_batch(2, force=True)
        # Flush the DB to generate job.id values.
        db_session.flush()

        assert es_helper.get(jobs) == {}

    def test_get_filters_out_duplicate_annotations(
        self, db_session, es_helper, factories, index
    ):
        annotation = factories.Annotation()
        index(annotation)
        # Two jobs for the same annotation.
        jobs = factories.SyncAnnotationJob.create_batch(2, annotation=annotation)
        # Flush the DB to generate job.id values.
        db_session.flush()

        result = es_helper.get(jobs)

        assert list(result.keys()) == [annotation.id]

    def test_get_doesnt_return_annotations_that_arent_in_the_search_index(
        self, db_session, es_helper, factories
    ):
        jobs = factories.SyncAnnotationJob.create_batch(1)
        # Flush the DB to generate job.id values.
        db_session.flush()

        assert es_helper.get(jobs) == {}

    def test_get_doesnt_return_annotations_that_have_been_marked_as_deleted_in_the_search_index(
        self, db_session, es_helper, factories, delete_from_elasticsearch
    ):
        annotation = factories.Annotation()
        job = factories.SyncAnnotationJob(annotation=annotation)
        # Flush the DB to generate job.id values.
        db_session.flush()
        delete_from_elasticsearch(annotation)

        assert es_helper.get([job]) == {}

    def test_get(self, db_session, es_helper, factories, index):
        annotations = factories.Annotation.create_batch(2)
        for annotation in annotations:
            index(annotation)
        jobs = [
            factories.SyncAnnotationJob(annotation=annotation)
            for annotation in annotations
        ]
        # An annotation with no job. This should be ignored.
        index(factories.Annotation())
        # Flush the DB to generate job.id values.
        db_session.flush()

        result = es_helper.get(jobs)

        assert result == {
            annotations[0].id: {
                "updated": annotations[0].updated,
                "user": annotations[0].userid,
            },
            annotations[1].id: {
                "updated": annotations[1].updated,
                "user": annotations[1].userid,
            },
        }

    @pytest.fixture
    def es_helper(self, es_client):
        return ESHelper(es_client)


class TestCounter:
    def test_annotation_synced(self, counter, db_session, factories):
        foo_jobs = factories.SyncAnnotationJob.create_batch(4, tag="foo")
        bar_jobs = factories.SyncAnnotationJob.create_batch(2, tag="bar")
        # Flush the DB to generate job.id values.
        db_session.flush()

        counter.annotation_synced(counter.Result.SYNCED_MISSING, foo_jobs[0])
        counter.annotation_synced(counter.Result.SYNCED_MISSING, bar_jobs[0])
        counter.annotation_synced(counter.Result.SYNCED_FORCED, foo_jobs[1])
        counter.annotation_synced(counter.Result.SYNCED_DIFFERENT, foo_jobs[2])
        counter.annotation_synced(counter.Result.SYNCED_MISSING, foo_jobs[3])
        counter.annotation_synced(counter.Result.SYNCED_DIFFERENT, bar_jobs[1])

        assert counter.counts == {
            counter.Result.SYNCED_MISSING.format(tag="foo"): 2,
            counter.Result.SYNCED_MISSING.format(tag="bar"): 1,
            counter.Result.SYNCED_FORCED.format(tag="foo"): 1,
            counter.Result.SYNCED_DIFFERENT.format(tag="foo"): 1,
            counter.Result.SYNCED_DIFFERENT.format(tag="bar"): 1,
            counter.Result.SYNCED_TAG_TOTAL.format(tag="foo"): 4,
            counter.Result.SYNCED_TAG_TOTAL.format(tag="bar"): 2,
            counter.Result.SYNCED_TOTAL: 6,
        }
        assert (
            counter.annotation_ids_to_sync
            == Any.list.containing(
                [url_safe_annotation_id(job) for job in foo_jobs + bar_jobs]
            ).only()
        )

    def test_annotation_synced_ignores_duplicates(self, counter, db_session, factories):
        # Two jobs for the same annotation.
        jobs = factories.SyncAnnotationJob.create_batch(
            2, annotation=factories.Annotation(), tag="foo"
        )
        # Flush the DB to generate job.id values.
        db_session.flush()

        counter.annotation_synced(counter.Result.SYNCED_MISSING, jobs[0])
        counter.annotation_synced(counter.Result.SYNCED_MISSING, jobs[1])

        assert counter.counts == {
            counter.Result.SYNCED_MISSING.format(tag="foo"): 1,
            counter.Result.SYNCED_TAG_TOTAL.format(tag="foo"): 1,
            counter.Result.SYNCED_TOTAL: 1,
        }
        assert counter.annotation_ids_to_sync == [url_safe_annotation_id(jobs[0])]

    def test_annotation_deleted(self, counter, db_session, factories):
        jobs = [
            *factories.SyncAnnotationJob.create_batch(2, tag="foo"),
            factories.SyncAnnotationJob(tag="bar"),
        ]
        # Flush the DB to generate job.id values.
        db_session.flush()

        counter.annotation_deleted(counter.Result.SYNCED_DELETED, jobs[0])
        counter.annotation_deleted(counter.Result.SYNCED_DELETED, jobs[1])
        counter.annotation_deleted(counter.Result.SYNCED_DELETED, jobs[2])

        assert counter.counts == {
            counter.Result.SYNCED_DELETED.format(tag="foo"): 2,
            counter.Result.SYNCED_DELETED.format(tag="bar"): 1,
            counter.Result.SYNCED_TAG_TOTAL.format(tag="foo"): 2,
            counter.Result.SYNCED_TAG_TOTAL.format(tag="bar"): 1,
            counter.Result.SYNCED_TOTAL: 3,
        }
        assert (
            counter.annotation_ids_to_delete
            == Any.list.containing([url_safe_annotation_id(job) for job in jobs]).only()
        )

    def test_job_completed(self, counter, db_session, factories):
        foo_jobs = factories.SyncAnnotationJob.create_batch(4, tag="foo")
        bar_jobs = factories.SyncAnnotationJob.create_batch(2, tag="bar")
        # Flush the DB to generate job.id values.
        db_session.flush()

        counter.job_completed(counter.Result.COMPLETED_UP_TO_DATE, foo_jobs[0])
        counter.job_completed(counter.Result.COMPLETED_UP_TO_DATE, bar_jobs[0])
        counter.job_completed(counter.Result.COMPLETED_FORCED, foo_jobs[1])
        counter.job_completed(counter.Result.COMPLETED_DELETED, foo_jobs[2])
        counter.job_completed(counter.Result.COMPLETED_UP_TO_DATE, foo_jobs[3])
        counter.job_completed(counter.Result.COMPLETED_DELETED, bar_jobs[1])

        assert counter.counts == {
            counter.Result.COMPLETED_UP_TO_DATE.format(tag="foo"): 2,
            counter.Result.COMPLETED_UP_TO_DATE.format(tag="bar"): 1,
            counter.Result.COMPLETED_FORCED.format(tag="foo"): 1,
            counter.Result.COMPLETED_DELETED.format(tag="foo"): 1,
            counter.Result.COMPLETED_DELETED.format(tag="bar"): 1,
            counter.Result.COMPLETED_TAG_TOTAL.format(tag="foo"): 4,
            counter.Result.COMPLETED_TAG_TOTAL.format(tag="bar"): 2,
            counter.Result.COMPLETED_TOTAL: 6,
        }
        assert counter.jobs_to_delete == Any.list.containing(foo_jobs + bar_jobs).only()

    def test_job_completed_ignores_duplicates(self, counter, db_session, factories):
        # Two jobs for the same annotation.
        job = factories.SyncAnnotationJob()
        # Flush the DB to generate job.id values.
        db_session.flush()

        counter.job_completed(counter.Result.COMPLETED_UP_TO_DATE, job)
        counter.job_completed(counter.Result.COMPLETED_UP_TO_DATE, job)

        assert counter.counts == {
            counter.Result.COMPLETED_UP_TO_DATE.format(tag=job.tag): 1,
            counter.Result.COMPLETED_TAG_TOTAL.format(tag=job.tag): 1,
            counter.Result.COMPLETED_TOTAL: 1,
        }
        assert counter.jobs_to_delete == [job]

    def test_annotation_synced_and_job_completed_together(
        self, counter, db_session, factories
    ):
        jobs = factories.SyncAnnotationJob.create_batch(2, tag="foo")
        # Flush the DB to generate job.id values.
        db_session.flush()

        counter.annotation_synced(counter.Result.SYNCED_MISSING, jobs[0])
        counter.job_completed(counter.Result.COMPLETED_UP_TO_DATE, jobs[1])

        assert counter.counts == {
            counter.Result.SYNCED_MISSING.format(tag="foo"): 1,
            counter.Result.SYNCED_TAG_TOTAL.format(tag="foo"): 1,
            counter.Result.SYNCED_TOTAL: 1,
            counter.Result.COMPLETED_UP_TO_DATE.format(tag="foo"): 1,
            counter.Result.COMPLETED_TAG_TOTAL.format(tag="foo"): 1,
            counter.Result.COMPLETED_TOTAL: 1,
        }

    @pytest.fixture
    def counter(self):
        return Counter()


class TestFactory:
    def test_it(
        self,
        AnnotationSyncService,
        BatchIndexer,
        DBHelper,
        ESHelper,
        db_session,
        pyramid_request,
        queue_service,
    ):
        svc = factory(sentinel.context, pyramid_request)

        BatchIndexer.assert_called_once_with(
            pyramid_request.db, pyramid_request.es, pyramid_request
        )
        DBHelper.assert_called_once_with(db=db_session)
        ESHelper.assert_called_once_with(es=pyramid_request.es)
        AnnotationSyncService.assert_called_once_with(
            batch_indexer=BatchIndexer.return_value,
            db_helper=DBHelper.return_value,
            es_helper=ESHelper.return_value,
            queue_service=queue_service,
        )
        assert svc == AnnotationSyncService.return_value

    @pytest.fixture(autouse=True)
    def AnnotationSyncService(self, patch):
        return patch("h.services.annotation_sync.AnnotationSyncService")

    @pytest.fixture(autouse=True)
    def BatchIndexer(self, patch):
        return patch("h.services.annotation_sync.BatchIndexer")

    @pytest.fixture(autouse=True)
    def DBHelper(self, patch):
        return patch("h.services.annotation_sync.DBHelper")

    @pytest.fixture(autouse=True)
    def ESHelper(self, patch):
        return patch("h.services.annotation_sync.ESHelper")

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.es = sentinel.es
        return pyramid_request


@pytest.fixture
def search_index_service(
    pyramid_request,
    es_client,
    moderation_service,  # pylint:disable=unused-argument
    nipsa_service,  # pylint:disable=unused-argument
):
    # Construct a real (not mock) SearchIndexService so we can call its
    # methods to index annotations.
    #
    # This isn't ideal because it means these AnnotationSyncService
    # unit tests are coupled to SearchIndexService and any other services
    # or code that SearchIndexService calls.
    #
    # On the other hand, this avoids these tests having to duplicate
    # SearchIndexService's code for indexing annotations and ensures that
    # the documents in the search index are the same as they would be in
    # production.
    #
    # (FIXME: The real solution to this issue is to refactor the services
    # to be more coherent and avoid this testing dilemma.)
    return SearchIndexService(
        request=pyramid_request,
        es=es_client,
        settings={},
        annotation_read_service=sentinel.annotation_read_service,
    )


@pytest.fixture
def index(search_index_service, es_client):
    """Return a method that indexes an annotation into Elasticsearch."""

    def index(annotation):
        """Index `annotation` into Elasticsearch."""
        search_index_service.add_annotation(annotation)
        es_client.conn.indices.refresh(index=es_client.index)

    return index


@pytest.fixture
def delete_from_elasticsearch(search_index_service, es_client):
    """Return a method that deletes an annotation from Elasticsearch."""

    def delete_from_elasticsearch(annotation):
        """Delete `annotation` from Elasticsearch."""
        search_index_service.delete_annotation_by_id(annotation.id)
        es_client.conn.indices.refresh(index=es_client.index)

    return delete_from_elasticsearch


def url_safe_annotation_id(job):
    """Return the URL-safe version of the given job's annotation ID."""
    return URLSafeUUID.hex_to_url_safe(job.kwargs["annotation_id"])
