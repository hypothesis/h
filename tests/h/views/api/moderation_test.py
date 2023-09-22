from unittest import mock

import pytest
from pyramid.httpexceptions import HTTPNoContent

from h.traversal import AnnotationContext
from h.views.api import moderation as views


class TestCreate:
    def test_it(
        self,
        pyramid_request,
        annotation_context,
        annotation_write_service,
        events,
        annotation,
    ):
        response = views.create(annotation_context, pyramid_request)

        annotation_write_service.hide.assert_called_once_with(
            annotation_context.annotation
        )
        events.AnnotationEvent.assert_called_once_with(
            pyramid_request, annotation.id, "update"
        )

        pyramid_request.notify_after_commit.assert_called_once_with(
            events.AnnotationEvent.return_value
        )
        assert isinstance(response, HTTPNoContent)


class TestDelete:
    def test_it(
        self,
        pyramid_request,
        annotation_context,
        annotation_write_service,
        events,
        annotation,
    ):
        response = views.delete(annotation_context, pyramid_request)

        annotation_write_service.unhide.assert_called_once_with(
            annotation_context.annotation
        )
        events.AnnotationEvent.assert_called_once_with(
            pyramid_request, annotation.id, "update"
        )

        pyramid_request.notify_after_commit.assert_called_once_with(
            events.AnnotationEvent.return_value
        )
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
