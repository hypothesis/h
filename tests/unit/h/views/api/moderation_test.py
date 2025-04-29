from unittest import mock

import pytest
from pyramid.httpexceptions import HTTPNoContent
from webob.multidict import MultiDict

from h.models import ModerationStatus
from h.traversal import AnnotationContext
from h.views.api import moderation as views


class TestHide:
    def test_it(
        self,
        pyramid_request,
        annotation_context,
        annotation_write_service,
        events,
        annotation,
    ):
        response = views.hide(annotation_context, pyramid_request)

        annotation_write_service.hide.assert_called_once_with(
            annotation_context.annotation, pyramid_request.user
        )
        events.AnnotationEvent.assert_called_once_with(
            pyramid_request, annotation.id, "update"
        )

        pyramid_request.notify_after_commit.assert_called_once_with(
            events.AnnotationEvent.return_value
        )
        assert isinstance(response, HTTPNoContent)


class TestUnhide:
    def test_it(
        self,
        pyramid_request,
        annotation_context,
        annotation_write_service,
        events,
        annotation,
    ):
        response = views.unhide(annotation_context, pyramid_request)

        annotation_write_service.unhide.assert_called_once_with(
            annotation_context.annotation, pyramid_request.user
        )
        events.AnnotationEvent.assert_called_once_with(
            pyramid_request, annotation.id, "update"
        )

        pyramid_request.notify_after_commit.assert_called_once_with(
            events.AnnotationEvent.return_value
        )
        assert isinstance(response, HTTPNoContent)


class TestChangeAnnotationModerationStatus:
    def test_it(
        self,
        pyramid_request,
        annotation_context,
        moderation_service,
        annotation_json_service,
        events,
        annotation,
    ):
        pyramid_request.params = MultiDict({"moderation_status": "SPAM"})

        response = views.change_annotation_moderation_status(
            annotation_context, pyramid_request
        )

        moderation_service.set_status.assert_called_once_with(
            annotation_context.annotation, pyramid_request.user, ModerationStatus.SPAM
        )
        events.AnnotationEvent.assert_called_once_with(
            pyramid_request, annotation.id, "update"
        )
        pyramid_request.notify_after_commit.assert_called_once_with(
            events.AnnotationEvent.return_value
        )
        annotation_json_service.present_for_user.assert_called_once_with(
            annotation=annotation, user=pyramid_request.user
        )
        assert response == annotation_json_service.present_for_user.return_value


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
