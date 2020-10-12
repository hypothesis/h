from unittest import mock
from unittest.mock import sentinel

import pytest

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


class TestSyncAnnotations:
    def test_it(self, search_index):
        indexer.sync_annotations("test_queue")

        search_index.sync.assert_called_once_with("test_queue")


pytestmark = pytest.mark.usefixtures("search_index")


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
