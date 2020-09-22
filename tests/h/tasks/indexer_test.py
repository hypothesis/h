import datetime
from unittest import mock
from unittest.mock import create_autospec, sentinel

import pytest
from h_matchers import Any

from h.services.search_index.service import SearchIndexService
from h.tasks import indexer


class TestSearchIndexServicesWrapperTasks:
    """Tests for tasks that just wrap SearchIndexServices functions."""

    def test_add_annotation(self, search_index):
        indexer.add_annotation(sentinel.annotation_id)

        search_index.add_annotation_by_id.assert_called_once_with(
            sentinel.annotation_id
        )

    def test_delete_annotation(self, search_index):
        indexer.delete_annotation(sentinel.annotation_id)

        search_index.delete_annotation_by_id.assert_called_once_with(
            sentinel.annotation_id
        )

    @pytest.fixture(autouse=True)
    def search_index(self, pyramid_config):
        search_index = create_autospec(SearchIndexService, instance=True)
        pyramid_config.register_service(search_index, name="search_index")

        return search_index


class TestReindexUserAnnotations:
    def test_it_creates_batch_indexer(self, BatchIndexer, annotation_ids, celery):
        userid = list(annotation_ids.keys())[0]

        indexer.reindex_user_annotations(userid)

        BatchIndexer.assert_any_call(
            celery.request.db, celery.request.es, celery.request
        )

    def test_it_reindexes_users_annotations(self, BatchIndexer, annotation_ids):
        userid = list(annotation_ids.keys())[0]

        indexer.reindex_user_annotations(userid)

        args, _ = BatchIndexer.return_value.index.call_args
        actual = args[0]
        expected = annotation_ids[userid]
        assert sorted(expected) == sorted(actual)

    @pytest.fixture
    def annotation_ids(self, factories):
        userid1 = "acct:jeannie@example.com"
        userid2 = "acct:bob@example.com"

        return {
            userid1: [
                a.id for a in factories.Annotation.create_batch(3, userid=userid1)
            ],
            userid2: [
                a.id for a in factories.Annotation.create_batch(2, userid=userid2)
            ],
        }


class TestReindexAnnotationsInDateRange:
    def test_it(self, BatchIndexer, celery, matching_annotations_ids):
        indexer.reindex_annotations_in_date_range(
            datetime.datetime.utcnow() - datetime.timedelta(days=7),
            datetime.datetime.utcnow(),
        )

        BatchIndexer.assert_called_once_with(
            celery.request.db, celery.request.es, celery.request,
        )
        BatchIndexer.return_value.index.assert_called_once_with(Any())
        indexed_annotations = list(BatchIndexer.return_value.index.call_args[0][0])
        assert sorted(indexed_annotations) == sorted(matching_annotations_ids)

    @pytest.fixture(autouse=True)
    def matching_annotations_ids(self, factories):
        """Annotations that're within the timeframe that we're reindexing."""
        return [
            annotation.id
            for annotation in factories.Annotation.create_batch(
                3, updated=datetime.datetime.utcnow() - datetime.timedelta(days=3)
            )
        ]

    @pytest.fixture(autouse=True)
    def not_matching_annotations(self, factories):
        """Annotations that're outside the timeframe that we're reindexing."""
        before_annotations = factories.Annotation.build_batch(
            3, updated=datetime.datetime.utcnow() - datetime.timedelta(days=14)
        )
        after_annotations = factories.Annotation.build_batch(
            3, updated=datetime.datetime.utcnow() + datetime.timedelta(days=14)
        )
        return before_annotations + after_annotations


@pytest.fixture(autouse=True)
def BatchIndexer(patch):
    return patch("h.tasks.indexer.BatchIndexer")


@pytest.fixture(autouse=True)
def celery(patch, pyramid_request):
    cel = patch("h.tasks.indexer.celery")
    cel.request = pyramid_request
    return cel


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.es = mock.Mock()
    return pyramid_request
