import datetime
from unittest import mock
from unittest.mock import create_autospec

import pytest
from h_matchers import Any

from h.services.search_index.service import SearchIndexService
from h.tasks import indexer


class FakeSettingsService:
    def __init__(self):
        self._data = {}

    def get(self, key):
        return self._data.get(key)

    def put(self, key, value):
        self._data[key] = value


class TestAddAnnotation:
    def test_it_fetches_the_annotation(self, storage, annotation, celery):
        id_ = "test-annotation-id"
        storage.fetch_annotation.return_value = annotation

        indexer.add_annotation(id_)

        storage.fetch_annotation.assert_called_once_with(celery.request.db, id_)

    def test_it_calls_index_with_annotation(self, storage, annotation, search_index):
        id_ = "test-annotation-id"
        storage.fetch_annotation.return_value = annotation

        indexer.add_annotation(id_)

        search_index.add_annotation.assert_any_call(annotation)

    def test_it_skips_indexing_when_annotation_cannot_be_loaded(
        self, storage, search_index
    ):
        storage.fetch_annotation.return_value = None

        indexer.add_annotation("test-annotation-id")

        assert search_index.add_annotation.called is False

    def test_during_reindex_adds_to_current_index(
        self, storage, annotation, search_index, settings_service
    ):
        settings_service.put("reindex.new_index", "hypothesis-xyz123")
        storage.fetch_annotation.return_value = annotation

        indexer.add_annotation("test-annotation-id")

        search_index.add_annotation.assert_any_call(
            annotation, target_index="hypothesis-xyz123",
        )

    def test_during_reindex_adds_to_new_index(
        self, storage, annotation, search_index, settings_service
    ):
        settings_service.put("reindex.new_index", "hypothesis-xyz123")
        storage.fetch_annotation.return_value = annotation

        indexer.add_annotation("test-annotation-id")

        search_index.add_annotation.assert_any_call(
            annotation, target_index="hypothesis-xyz123",
        )

    def test_it_indexes_thread_root(self, storage, reply, delay):
        storage.fetch_annotation.return_value = reply

        indexer.add_annotation("test-annotation-id")

        delay.assert_called_once_with("root-id")

    @pytest.fixture
    def annotation(self):
        return mock.Mock(spec_set=["is_reply"], is_reply=False)

    @pytest.fixture
    def reply(self):
        return mock.Mock(
            spec_set=["is_reply", "thread_root_id"],
            is_reply=True,
            thread_root_id="root-id",
        )

    @pytest.fixture
    def delay(self, patch):
        return patch("h.tasks.indexer.add_annotation.delay")


class TestDeleteAnnotation:
    def test_it_deletes_from_index(self, search_index):
        id_ = "test-annotation-id"
        indexer.delete_annotation(id_)

        search_index.delete_annotation_by_id.assert_any_call(id_)

    def test_during_reindex_deletes_from_current_index(
        self, search_index, settings_service
    ):
        settings_service.put("reindex.new_index", "hypothesis-xyz123")

        indexer.delete_annotation("test-annotation-id")

        search_index.delete_annotation_by_id.assert_any_call(
            "test-annotation-id", target_index="hypothesis-xyz123"
        )

    def test_during_reindex_deletes_from_new_index(
        self, search_index, settings_service
    ):
        settings_service.put("reindex.new_index", "hypothesis-xyz123")

        indexer.delete_annotation("test-annotation-id")

        search_index.delete_annotation_by_id.assert_any_call(
            "test-annotation-id", target_index="hypothesis-xyz123"
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


pytestmark = pytest.mark.usefixtures("settings_service")


@pytest.fixture(autouse=True)
def search_index(pyramid_config):
    search_index = create_autospec(SearchIndexService, instance=True)
    pyramid_config.register_service(search_index, name="search_index")

    return search_index


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


@pytest.fixture
def settings_service(pyramid_config):
    service = FakeSettingsService()
    pyramid_config.register_service(service, name="settings")
    return service


@pytest.fixture(autouse=True)
def storage(patch):
    return patch("h.tasks.indexer.storage")
