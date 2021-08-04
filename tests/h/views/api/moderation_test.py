from unittest import mock

import pytest
from pyramid.httpexceptions import HTTPNoContent

from h.models import AnnotationModeration
from h.traversal import AnnotationContext
from h.views.api import moderation as views


class TestCreate:
    def test_it_hides_the_annotation(
        self, pyramid_request, annotation, annotation_context
    ):
        annotation.moderation = None

        views.create(annotation_context, pyramid_request)

        assert annotation.is_hidden

    def test_it_does_not_modify_an_already_hidden_annotation(
        self, pyramid_request, annotation, annotation_context
    ):
        moderation = AnnotationModeration()
        annotation.moderation = moderation

        views.create(annotation_context, pyramid_request)

        assert annotation.is_hidden
        # It's the same one not a new one
        assert annotation.moderation == moderation

    def test_it_publishes_update_event(
        self, pyramid_request, annotation_context, events
    ):
        views.create(annotation_context, pyramid_request)

        events.AnnotationEvent.assert_called_once_with(
            pyramid_request, annotation_context.annotation.id, "update"
        )

        pyramid_request.notify_after_commit.assert_called_once_with(
            events.AnnotationEvent.return_value
        )

    def test_it_renders_no_content(self, pyramid_request, annotation_context):
        response = views.create(annotation_context, pyramid_request)
        assert isinstance(response, HTTPNoContent)


class TestDelete:
    def test_it_unhides_the_annotation(
        self, pyramid_request, annotation, annotation_context
    ):
        annotation.moderation = AnnotationModeration()

        views.delete(annotation_context, pyramid_request)

        assert not annotation.is_hidden

    def test_it_publishes_update_event(
        self, pyramid_request, annotation_context, events
    ):
        views.delete(annotation_context, pyramid_request)

        events.AnnotationEvent.assert_called_once_with(
            pyramid_request, annotation_context.annotation.id, "update"
        )

        pyramid_request.notify_after_commit.assert_called_once_with(
            events.AnnotationEvent.return_value
        )

    def test_it_renders_no_content(self, pyramid_request, annotation_context):
        response = views.delete(annotation_context, pyramid_request)
        assert isinstance(response, HTTPNoContent)


@pytest.fixture
def annotation(factories):
    return factories.Annotation()


@pytest.fixture
def annotation_context(annotation):
    return AnnotationContext(annotation)


@pytest.fixture
def events(patch):
    return patch("h.views.api.moderation.events")


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.notify_after_commit = mock.Mock()
    return pyramid_request
