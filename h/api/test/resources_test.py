# -*- coding: utf-8 -*-

from mock import Mock
from mock import patch
from pyramid.testing import DummyRequest
import pytest

from h.api.resources import AnnotationFactory


class TestAnnotationFactory(object):
    def test_get_item_fetches_annotation(self, storage):
        factory = AnnotationFactory(DummyRequest())

        factory['123']
        storage.fetch_annotation.assert_called_once_with('123')

    def test_get_item_returns_annotation(self, storage):
        factory = AnnotationFactory(DummyRequest())
        storage.fetch_annotation.return_value = Mock()

        annotation = factory['123']
        assert annotation == storage.fetch_annotation.return_value

    def test_get_item_raises_when_annotation_is_not_found(self, storage):
        factory = AnnotationFactory(DummyRequest())
        storage.fetch_annotation.return_value = None

        with pytest.raises(KeyError):
            factory['123']

    @pytest.fixture
    def storage(self, request):
        patcher = patch('h.api.resources.storage', autospec=True)
        module = patcher.start()
        request.addfinalizer(patcher.stop)
        return module
