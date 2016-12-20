# -*- coding: utf-8 -*-

import mock
import pytest

from h.indexer.reindexer import SETTING_NEW_INDEX
from h.tasks import indexer


class FakeSettingsService(object):
    def __init__(self):
        self._data = {}

    def get(self, key):
        return self._data.get(key)

    def put(self, key, value):
        self._data[key] = value


@pytest.mark.usefixtures('celery', 'index', 'settings_service')
class TestAddAnnotation(object):

    def test_it_fetches_the_annotation(self, fetch_annotation, celery):
        id_ = 'test-annotation-id'

        indexer.add_annotation(id_)

        fetch_annotation.assert_called_once_with(celery.request.db, id_)

    def test_it_calls_index_with_annotation(self, fetch_annotation, index, celery):
        id_ = 'test-annotation-id'
        annotation = mock.Mock(id=id_)
        fetch_annotation.return_value = annotation

        indexer.add_annotation(id_)

        index.assert_called_once_with(celery.request.es, annotation, celery.request)

    def test_it_skips_indexing_when_annotation_cannot_be_loaded(self, fetch_annotation, index, celery):
        fetch_annotation.return_value = None

        indexer.add_annotation('test-annotation-id')

        assert index.called is False

    def test_during_reindex_adds_to_current_index(self, fetch_annotation, index, celery, settings_service):
        settings_service.put(SETTING_NEW_INDEX, 'hypothesis-abcdef123')
        fetch_annotation.return_value = mock.sentinel.annotation

        indexer.add_annotation('test-annotation-id')

        index.assert_any_call(celery.request.es,
                              mock.sentinel.annotation,
                              celery.request)

    def test_during_reindex_adds_to_new_index(self, fetch_annotation, index, celery, settings_service):
        settings_service.put(SETTING_NEW_INDEX, 'hypothesis-abcdef123')
        fetch_annotation.return_value = mock.sentinel.annotation

        indexer.add_annotation('test-annotation-id')

        index.assert_any_call(celery.request.es,
                              mock.sentinel.annotation,
                              celery.request,
                              target_index='hypothesis-abcdef123')

    @pytest.fixture
    def index(self, patch):
        return patch('h.tasks.indexer.index')

    @pytest.fixture
    def fetch_annotation(self, patch):
        return patch('h.tasks.indexer.storage.fetch_annotation')


@pytest.mark.usefixtures('celery', 'delete', 'settings_service')
class TestDeleteAnnotation(object):

    def test_it_deletes_from_index(self, delete, celery):
        id_ = 'test-annotation-id'
        indexer.delete_annotation(id_)

        delete.assert_called_once_with(celery.request.es, id_)

    def test_during_reindex_deletes_from_current_index(self, delete, celery, settings_service):
        settings_service.put(SETTING_NEW_INDEX, 'hypothesis-abcdef123')

        indexer.delete_annotation('test-annotation-id')

        delete.assert_any_call(celery.request.es,
                               'test-annotation-id')

    def test_during_reindex_deletes_from_new_index(self, delete, celery, settings_service):
        settings_service.put(SETTING_NEW_INDEX, 'hypothesis-abcdef123')

        indexer.delete_annotation('test-annotation-id')

        delete.assert_any_call(celery.request.es,
                               'test-annotation-id',
                               target_index='hypothesis-abcdef123')

    @pytest.fixture
    def delete(self, patch):
        return patch('h.tasks.indexer.delete')


@pytest.fixture
def celery(patch, pyramid_request):
    cel = patch('h.tasks.indexer.celery')
    cel.request = pyramid_request
    return cel


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.es = mock.Mock()
    return pyramid_request


@pytest.fixture
def settings_service(pyramid_config):
    service = FakeSettingsService()
    pyramid_config.register_service(service, name='settings')
    return service
