from datetime import UTC, datetime
from unittest import mock

import pytest
from pyramid import httpexceptions
from pyramid.httpexceptions import HTTPNoContent

from h.models import ModerationStatus
from h.schemas.base import ValidationError
from h.traversal import AnnotationContext
from h.views.api import moderation as views


class TestHide:
    def test_it(
        self,
        pyramid_request,
        annotation_context,
        moderation_service,
        events,
        annotation,
    ):
        response = views.hide(annotation_context, pyramid_request)

        moderation_service.set_status.assert_called_once_with(
            annotation_context.annotation, ModerationStatus.SPAM, pyramid_request.user
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
        moderation_service,
        events,
        annotation,
    ):
        response = views.unhide(annotation_context, pyramid_request)

        moderation_service.set_status.assert_called_once_with(
            annotation_context.annotation,
            ModerationStatus.APPROVED,
            pyramid_request.user,
        )

        events.AnnotationEvent.assert_called_once_with(
            pyramid_request, annotation.id, "update"
        )

        pyramid_request.notify_after_commit.assert_called_once_with(
            events.AnnotationEvent.return_value
        )
        assert isinstance(response, HTTPNoContent)


class TestChangeAnnotationModerationStatus:
    @pytest.mark.parametrize(
        "moderation_status,current_moderation_status",
        [
            (None, None),
            #  When current_moderation_status is not provided, we can set any moderation status safely
            (ModerationStatus.APPROVED, None),
            #  When current_moderation_status is provided, it needs to match current annotation's status
            (ModerationStatus.APPROVED, ModerationStatus.DENIED),
            #  If current_moderation_status does not match the actual current value, but the one we want to set does,
            #  that is also considered valid
            (ModerationStatus.DENIED, ModerationStatus.PENDING),
        ],
    )
    def test_it(
        self,
        pyramid_request,
        moderated_annotation_context,
        moderation_service,
        annotation_json_service,
        events,
        annotation,
        valid_payload,
        factories,
        moderation_status,
        current_moderation_status,
    ):
        if moderation_status is not None:
            valid_payload["moderation_status"] = moderation_status.value
        if current_moderation_status is not None:
            valid_payload["current_moderation_status"] = current_moderation_status.value

        pyramid_request.json_body = valid_payload
        moderation_service.set_status.return_value = factories.ModerationLog()

        response = views.change_annotation_moderation_status(
            moderated_annotation_context, pyramid_request
        )

        moderation_service.set_status.assert_called_once_with(
            moderated_annotation_context.annotation,
            moderation_status
            if moderation_status is not None
            else ModerationStatus.SPAM,
            pyramid_request.user,
        )
        events.AnnotationEvent.assert_called_once_with(
            pyramid_request, annotation.id, "update"
        )
        events.ModeratedAnnotationEvent.assert_called_once_with(
            pyramid_request, moderation_service.set_status.return_value.id
        )
        pyramid_request.notify_after_commit.assert_has_calls(
            [
                mock.call(events.AnnotationEvent.return_value),
                mock.call(events.ModeratedAnnotationEvent.return_value),
            ]
        )
        annotation_json_service.present_for_user.assert_called_once_with(
            annotation=annotation, user=pyramid_request.user
        )
        assert response == annotation_json_service.present_for_user.return_value

    @pytest.mark.parametrize(
        "annotation_updated,message",
        [
            (None, "annotation_updated: Required"),
            ("BAD DATE", "annotation_updated: Invalid date"),
        ],
    )
    def test_invalid_annotation_updated(
        self,
        valid_payload,
        annotation_updated,
        message,
        moderated_annotation_context,
        pyramid_request,
    ):
        valid_payload["annotation_updated"] = annotation_updated
        pyramid_request.json_body = valid_payload

        with pytest.raises(ValidationError) as excinfo:
            views.change_annotation_moderation_status(
                moderated_annotation_context, pyramid_request
            )

        assert str(excinfo.value) == message

    def test_outdated(
        self,
        valid_payload,
        moderated_annotation_context,
        pyramid_request,
    ):
        valid_payload["annotation_updated"] = "2020-10-01T12:00:00Z"
        pyramid_request.json_body = valid_payload

        with pytest.raises(httpexceptions.HTTPConflict) as excinfo:
            views.change_annotation_moderation_status(
                moderated_annotation_context, pyramid_request
            )

        assert (
            str(excinfo.value)
            == "The annotation has been updated since the moderation status was set."
        )

    def test_conflicting_prev_status(
        self,
        valid_payload_with_prev_status,
        moderated_annotation_context,
        pyramid_request,
    ):
        pyramid_request.json_body = valid_payload_with_prev_status

        with pytest.raises(httpexceptions.HTTPConflict) as excinfo:
            views.change_annotation_moderation_status(
                moderated_annotation_context, pyramid_request
            )

        assert (
            str(excinfo.value)
            == "The annotation has been moderated since it was loaded."
        )

    @pytest.fixture
    def valid_payload(self, annotation):
        return {
            "moderation_status": "SPAM",
            "annotation_updated": annotation.updated.isoformat(),
        }

    @pytest.fixture
    def valid_payload_with_prev_status(self, valid_payload):
        valid_payload["current_moderation_status"] = "APPROVED"
        return valid_payload

    @pytest.fixture
    def moderated_annotation_context(self, annotation_context):
        annotation_context.annotation.moderation_status = ModerationStatus.DENIED
        return annotation_context


@pytest.fixture
def annotation(factories):
    return factories.Annotation(updated=datetime(2023, 10, 1, 12, 0, 0, tzinfo=UTC))


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
