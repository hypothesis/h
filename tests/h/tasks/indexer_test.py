# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from h.tasks import indexer


class FakeSettingsService(object):
    def __init__(self):
        self._data = {}

    def get(self, key):
        return self._data.get(key)

    def put(self, key, value):
        self._data[key] = value


@pytest.mark.usefixtures("celery", "index", "settings_service")
class TestAddAnnotation(object):
    def test_it_fetches_the_annotation(self, fetch_annotation, annotation, celery):
        id_ = "test-annotation-id"
        fetch_annotation.return_value = annotation

        indexer.add_annotation(id_)

        fetch_annotation.assert_called_once_with(celery.request.db, id_)

    def test_it_calls_index_with_annotation(
        self, fetch_annotation, annotation, index, celery
    ):
        id_ = "test-annotation-id"
        fetch_annotation.return_value = annotation

        indexer.add_annotation(id_)

        index.assert_any_call(celery.request.es, annotation, celery.request)

    def test_it_skips_indexing_when_annotation_cannot_be_loaded(
        self, fetch_annotation, index, celery
    ):
        fetch_annotation.return_value = None

        indexer.add_annotation("test-annotation-id")

        assert index.called is False

    def test_during_reindex_adds_to_current_index(
        self, fetch_annotation, annotation, index, celery, settings_service
    ):
        settings_service.put("reindex.new_index", "hypothesis-xyz123")
        fetch_annotation.return_value = annotation

        indexer.add_annotation("test-annotation-id")

        index.assert_any_call(
            celery.request.es,
            annotation,
            celery.request,
            target_index="hypothesis-xyz123",
        )

    def test_during_reindex_adds_to_new_index(
        self, fetch_annotation, annotation, index, celery, settings_service
    ):
        settings_service.put("reindex.new_index", "hypothesis-xyz123")
        fetch_annotation.return_value = annotation

        indexer.add_annotation("test-annotation-id")

        index.assert_any_call(
            celery.request.es,
            annotation,
            celery.request,
            target_index="hypothesis-xyz123",
        )

    def test_it_indexes_thread_root(self, fetch_annotation, reply, delay):
        fetch_annotation.return_value = reply

        indexer.add_annotation("test-annotation-id")

        delay.assert_called_once_with("root-id")

    @pytest.fixture
    def index(self, patch):
        return patch("h.tasks.indexer.index")

    @pytest.fixture
    def fetch_annotation(self, patch):
        return patch("h.tasks.indexer.storage.fetch_annotation")

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


@pytest.mark.usefixtures("celery", "delete", "settings_service")
class TestDeleteAnnotation(object):
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

    @pytest.fixture
    def delete(self, patch):
        return patch("h.tasks.indexer.delete")


@pytest.mark.usefixtures("celery")
class TestReindexUserAnnotations(object):
    def test_it_creates_batch_indexer(self, batch_indexer, annotation_ids, celery):
        userid = list(annotation_ids.keys())[0]

        indexer.reindex_user_annotations(userid)

        batch_indexer.assert_any_call(
            celery.request.db, celery.request.es, celery.request
        )

    def test_it_reindexes_users_annotations(self, batch_indexer, annotation_ids):
        userid = list(annotation_ids.keys())[0]

        indexer.reindex_user_annotations(userid)

        args, _ = batch_indexer.return_value.index.call_args
        actual = args[0]
        expected = annotation_ids[userid]
        assert sorted(expected) == sorted(actual)

    @pytest.fixture
    def batch_indexer(self, patch):
        return patch("h.tasks.indexer.BatchIndexer")

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


@pytest.fixture
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
