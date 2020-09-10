from unittest import mock

import pytest

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

    def test_it_calls_index_with_annotation(self, storage, annotation, index, celery):
        id_ = "test-annotation-id"
        storage.fetch_annotation.return_value = annotation

        indexer.add_annotation(id_)

        index.assert_any_call(celery.request.es, annotation, celery.request)

    def test_it_skips_indexing_when_annotation_cannot_be_loaded(
        self, storage, index, celery
    ):
        storage.fetch_annotation.return_value = None

        indexer.add_annotation("test-annotation-id")

        assert index.called is False

    def test_during_reindex_adds_to_current_index(
        self, storage, annotation, index, celery, settings_service
    ):
        settings_service.put("reindex.new_index", "hypothesis-xyz123")
        storage.fetch_annotation.return_value = annotation

        indexer.add_annotation("test-annotation-id")

        index.assert_any_call(
            celery.request.es,
            annotation,
            celery.request,
            target_index="hypothesis-xyz123",
        )

    def test_during_reindex_adds_to_new_index(
        self, storage, annotation, index, celery, settings_service
    ):
        settings_service.put("reindex.new_index", "hypothesis-xyz123")
        storage.fetch_annotation.return_value = annotation

        indexer.add_annotation("test-annotation-id")

        index.assert_any_call(
            celery.request.es,
            annotation,
            celery.request,
            target_index="hypothesis-xyz123",
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
    def test_it_deletes_from_index(self, delete, celery):
        id_ = "test-annotation-id"
        indexer.delete_annotation(id_)

        delete.assert_any_call(celery.request.es, id_)

    def test_during_reindex_deletes_from_current_index(
        self, delete, celery, settings_service
    ):
        settings_service.put("reindex.new_index", "hypothesis-xyz123")

        indexer.delete_annotation("test-annotation-id")

        delete.assert_any_call(
            celery.request.es, "test-annotation-id", target_index="hypothesis-xyz123"
        )

    def test_during_reindex_deletes_from_new_index(
        self, delete, celery, settings_service
    ):
        settings_service.put("reindex.new_index", "hypothesis-xyz123")

        indexer.delete_annotation("test-annotation-id")

        delete.assert_any_call(
            celery.request.es, "test-annotation-id", target_index="hypothesis-xyz123"
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


pytestmark = pytest.mark.usefixtures("settings_service")


@pytest.fixture(autouse=True)
def BatchIndexer(patch):
    return patch("h.tasks.indexer.BatchIndexer")


@pytest.fixture(autouse=True)
def celery(patch, pyramid_request):
    cel = patch("h.tasks.indexer.celery")
    cel.request = pyramid_request
    return cel


@pytest.fixture(autouse=True)
def delete(patch):
    return patch("h.tasks.indexer.delete")


@pytest.fixture(autouse=True)
def index(patch):
    return patch("h.tasks.indexer.index")


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
