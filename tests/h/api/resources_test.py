# -*- coding: utf-8 -*-

from mock import Mock
import pytest

from h.api.resources import AnnotationFactory


class TestAnnotationFactory(object):
    def test_get_item_fetches_annotation(self, pyramid_request, storage):
        factory = AnnotationFactory(pyramid_request)

        factory['123']
        storage.fetch_annotation.assert_called_once_with(pyramid_request.db, '123')

    def test_get_item_returns_annotation(self, pyramid_request, storage):
        factory = AnnotationFactory(pyramid_request)
        storage.fetch_annotation.return_value = Mock()

        annotation = factory['123']
        assert annotation == storage.fetch_annotation.return_value

    def test_get_item_raises_when_annotation_is_not_found(self, storage, pyramid_request):
        factory = AnnotationFactory(pyramid_request)
        storage.fetch_annotation.return_value = None

        with pytest.raises(KeyError):
            factory['123']

    @pytest.fixture
    def storage(self, patch):
        return patch('h.api.resources.storage')
