# -*- coding: utf-8 -*-

import mock
import pytest

from h.tasks import indexer


@pytest.mark.usefixtures('celery', 'index')
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

    @pytest.fixture
    def index(self, patch):
        return patch('h.tasks.indexer.index')

    @pytest.fixture
    def fetch_annotation(self, patch):
        return patch('h.tasks.indexer.storage.fetch_annotation')


@pytest.mark.usefixtures('celery', 'delete')
class TestDeleteAnnotation(object):

    def test_it_deletes_from_index(self, delete, celery):
        id_ = 'test-annotation-id'
        indexer.delete_annotation(id_)

        delete.assert_called_once_with(celery.request.es, id_)

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
