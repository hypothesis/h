# -*- coding: utf-8 -*-

from mock import Mock
from pyramid.testing import DummyRequest
import pytest

from h.api.resources import AnnotationFactory


class TestAnnotationFactory(object):
    def test_get_item_fetches_annotation(self, storage, mock_request):
        factory = AnnotationFactory(mock_request)

        factory['123']
        storage.fetch_annotation.assert_called_once_with(mock_request.db, '123')

    def test_get_item_returns_annotation(self, storage, mock_request):
        factory = AnnotationFactory(mock_request)
        storage.fetch_annotation.return_value = Mock()

        annotation = factory['123']
        assert annotation == storage.fetch_annotation.return_value

    def test_get_item_raises_when_annotation_is_not_found(self, storage, mock_request):
        factory = AnnotationFactory(mock_request)
        storage.fetch_annotation.return_value = None

        with pytest.raises(KeyError):
            factory['123']

    @pytest.fixture
    def mock_request(self):
        return DummyRequest(db=Mock())

    @pytest.fixture
    def storage(self, patch):
        return patch('h.api.resources.storage')
