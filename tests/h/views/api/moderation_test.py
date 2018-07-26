# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from pyramid.httpexceptions import HTTPNoContent, HTTPNotFound

from h.views.api import moderation as views


@pytest.mark.usefixtures('moderation_service', 'has_permission')
class TestCreate(object):
    def test_it_hides_the_annotation(self, pyramid_request, resource, moderation_service):
        views.create(resource, pyramid_request)

        moderation_service.hide.assert_called_once_with(resource.annotation)

    def test_it_publishes_update_event(self, pyramid_request, resource, events):
        views.create(resource, pyramid_request)

        events.AnnotationEvent.assert_called_once_with(
            pyramid_request, resource.annotation.id, 'update')

        pyramid_request.notify_after_commit.assert_called_once_with(
            events.AnnotationEvent.return_value)

    def test_it_renders_no_content(self, pyramid_request, resource):
        response = views.create(resource, pyramid_request)
        assert isinstance(response, HTTPNoContent)

    def test_it_checks_for_group_admin_permission(self, pyramid_request, resource):
        views.create(resource, pyramid_request)
        pyramid_request.has_permission.assert_called_once_with('admin', resource.group)

    def test_it_responds_with_not_found_when_no_admin_access_in_group(self, pyramid_request, resource):
        pyramid_request.has_permission.return_value = False
        with pytest.raises(HTTPNotFound):
            views.create(resource, pyramid_request)


@pytest.mark.usefixtures('moderation_service', 'has_permission')
class TestDelete(object):
    def test_it_unhides_the_annotation(self, pyramid_request, resource, moderation_service):
        views.delete(resource, pyramid_request)

        moderation_service.unhide.assert_called_once_with(resource.annotation)

    def test_it_publishes_update_event(self, pyramid_request, resource, events):
        views.delete(resource, pyramid_request)

        events.AnnotationEvent.assert_called_once_with(
            pyramid_request, resource.annotation.id, 'update')

        pyramid_request.notify_after_commit.assert_called_once_with(
            events.AnnotationEvent.return_value)

    def test_it_renders_no_content(self, pyramid_request, resource):
        response = views.delete(resource, pyramid_request)
        assert isinstance(response, HTTPNoContent)

    def test_it_checks_for_group_admin_permission(self, pyramid_request, resource):
        views.delete(resource, pyramid_request)
        pyramid_request.has_permission.assert_called_once_with('admin', resource.group)

    def test_it_responds_with_not_found_when_no_admin_access_in_group(self, pyramid_request, resource):
        pyramid_request.has_permission.return_value = False
        with pytest.raises(HTTPNotFound):
            views.delete(resource, pyramid_request)


@pytest.fixture
def resource():
    return mock.Mock(spec_set=['annotation', 'group'])


@pytest.fixture
def moderation_service(pyramid_config):
    svc = mock.Mock(spec_set=['hide', 'unhide'])
    pyramid_config.register_service(svc, name='annotation_moderation')
    return svc


@pytest.fixture
def has_permission(pyramid_request):
    func = mock.Mock(return_value=True)
    pyramid_request.has_permission = func
    return func


@pytest.fixture
def events(patch):
    return patch('h.views.api.moderation.events')


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.notify_after_commit = mock.Mock()
    return pyramid_request
