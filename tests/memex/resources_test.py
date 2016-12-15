# -*- coding: utf-8 -*-

from mock import Mock
import pytest

from pyramid import security

from memex.resources import AnnotationResourceFactory, AnnotationResource


class TestAnnotationResourceFactory(object):
    def test_get_item_fetches_annotation(self, pyramid_request, storage):
        factory = AnnotationResourceFactory(pyramid_request)

        factory['123']
        storage.fetch_annotation.assert_called_once_with(pyramid_request.db, '123')

    def test_get_item_returns_annotation_resource(self, pyramid_request, storage):
        factory = AnnotationResourceFactory(pyramid_request)
        storage.fetch_annotation.return_value = Mock()

        resource = factory['123']
        assert isinstance(resource, AnnotationResource)

    def test_get_item_resource_has_right_annotation(self, pyramid_request, storage):
        factory = AnnotationResourceFactory(pyramid_request)
        storage.fetch_annotation.return_value = Mock()

        resource = factory['123']
        assert resource.annotation == storage.fetch_annotation.return_value

    def test_get_item_raises_when_annotation_is_not_found(self, storage, pyramid_request):
        factory = AnnotationResourceFactory(pyramid_request)
        storage.fetch_annotation.return_value = None

        with pytest.raises(KeyError):
            factory['123']

    @pytest.fixture
    def storage(self, patch):
        return patch('memex.resources.storage')


class TestAnnotationResource(object):
    def test_acl_private(self, factories, pyramid_request):
        ann = factories.Annotation(shared=False, userid='saoirse')
        res = AnnotationResource(pyramid_request, ann)
        actual = res.__acl__()
        expect = [(security.Allow, 'saoirse', 'read'),
                  (security.Allow, 'saoirse', 'admin'),
                  (security.Allow, 'saoirse', 'update'),
                  (security.Allow, 'saoirse', 'delete'),
                  security.DENY_ALL]
        assert actual == expect

    def test_acl_world_shared(self, factories, pyramid_request):
        ann = factories.Annotation(shared=True, userid='saoirse', groupid='__world__')
        res = AnnotationResource(pyramid_request, ann)
        actual = res.__acl__()
        expect = [(security.Allow, security.Everyone, 'read'),
                  (security.Allow, 'saoirse', 'admin'),
                  (security.Allow, 'saoirse', 'update'),
                  (security.Allow, 'saoirse', 'delete'),
                  security.DENY_ALL]
        assert actual == expect

    def test_acl_group_shared(self, factories, pyramid_request):
        ann = factories.Annotation(shared=True, userid='saoirse', groupid='lulapalooza')
        res = AnnotationResource(pyramid_request, ann)
        actual = res.__acl__()
        expect = [(security.Allow, 'group:lulapalooza', 'read'),
                  (security.Allow, 'saoirse', 'admin'),
                  (security.Allow, 'saoirse', 'update'),
                  (security.Allow, 'saoirse', 'delete'),
                  security.DENY_ALL]
        assert actual == expect
