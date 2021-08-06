from unittest import mock

import pytest
from pyramid.httpexceptions import HTTPNoContent

from h.views.api import moderation as views


@pytest.mark.usefixtures("moderation_service")
class TestCreate:
    def test_it_hides_the_annotation(
        self, pyramid_request, resource, moderation_service
    ):
        views.create(resource, pyramid_request)

        moderation_service.hide.assert_called_once_with(resource.annotation)

    def test_it_publishes_update_event(self, pyramid_request, resource, events):
        views.create(resource, pyramid_request)

        events.AnnotationEvent.assert_called_once_with(
            pyramid_request, resource.annotation.id, "update"
        )

        pyramid_request.notify_after_commit.assert_called_once_with(
            events.AnnotationEvent.return_value
        )

    def test_it_renders_no_content(self, pyramid_request, resource):
        response = views.create(resource, pyramid_request)
        assert isinstance(response, HTTPNoContent)


@pytest.mark.usefixtures("moderation_service")
class TestDelete:
    def test_it_unhides_the_annotation(
        self, pyramid_request, resource, moderation_service
    ):
        views.delete(resource, pyramid_request)

        moderation_service.unhide.assert_called_once_with(resource.annotation)

    def test_it_publishes_update_event(self, pyramid_request, resource, events):
        views.delete(resource, pyramid_request)

        events.AnnotationEvent.assert_called_once_with(
            pyramid_request, resource.annotation.id, "update"
        )

        pyramid_request.notify_after_commit.assert_called_once_with(
            events.AnnotationEvent.return_value
        )

    def test_it_renders_no_content(self, pyramid_request, resource):
        response = views.delete(resource, pyramid_request)
        assert isinstance(response, HTTPNoContent)


@pytest.fixture
def resource():
    return mock.Mock(spec_set=["annotation", "group"])


@pytest.fixture
def events(patch):
    return patch("h.views.api.moderation.events")


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.notify_after_commit = mock.Mock()
    return pyramid_request
