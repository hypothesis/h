from unittest import mock
from unittest.mock import sentinel

import pytest
from h_matchers import Any

from h.security.permissions import Permission
from h.services.annotation_json_presentation import AnnotationJSONPresentationService


class TestAnnotationJSONPresentationService:
    def test_it_configures_formatters(
        self,
        svc,
        formatters,
        db_session,
        flag_service,
        moderation_service,
        has_permission,
    ):
        formatters.AnnotationFlagFormatter.assert_called_once_with(
            sentinel.flag_svc, sentinel.user
        )
        formatters.AnnotationHiddenFormatter.assert_called_once_with(
            sentinel.moderation_svc, Any.function(), sentinel.user
        )
        formatters.AnnotationModerationFormatter.assert_called_once_with(
            sentinel.flag_count_svc, sentinel.user, has_permission
        )
        formatters.AnnotationUserInfoFormatter.assert_called_once_with(
            db_session, sentinel.user_svc
        )

        assert svc.formatters == [
            formatters.AnnotationFlagFormatter.return_value,
            formatters.AnnotationHiddenFormatter.return_value,
            formatters.AnnotationModerationFormatter.return_value,
            formatters.AnnotationUserInfoFormatter.return_value,
        ]

    def test_hidden_status_included_if_user_can_moderate_group(
        self, formatters, has_permission, svc
    ):
        group = mock.Mock()
        moderator_check = formatters.AnnotationHiddenFormatter.call_args[0][1]
        moderator_check(group)
        has_permission.assert_called_once_with(Permission.Group.MODERATE, group)

    def test_present(self, svc, AnnotationJSONPresenter, annotation_resource):
        result = svc.present(annotation_resource)

        AnnotationJSONPresenter.assert_called_once_with(
            annotation_resource, svc.formatters
        )

        assert result == AnnotationJSONPresenter.return_value.asdict.return_value

    def test_present_all(
        self, svc, factories, AnnotationJSONPresenter, AnnotationContext
    ):
        annotation = factories.Annotation()
        annotation_ids = [annotation.id]

        result = svc.present_all(annotation_ids)

        for formatter in svc.formatters:
            formatter.preload.assert_called_once_with(annotation_ids)

        AnnotationContext.assert_called_once_with(
            annotation, svc.group_svc, svc.links_svc
        )
        AnnotationJSONPresenter.assert_called_once_with(
            AnnotationContext.return_value, svc.formatters
        )
        assert result == [
            AnnotationJSONPresenter.return_value.asdict.return_value,
        ]

    @pytest.fixture
    def svc(self, db_session, has_permission):
        return AnnotationJSONPresentationService(
            session=db_session,
            user=sentinel.user,
            group_svc=sentinel.group_svc,
            links_svc=sentinel.links_svc,
            flag_svc=sentinel.flag_svc,
            flag_count_svc=sentinel.flag_count_svc,
            moderation_svc=sentinel.moderation_svc,
            user_svc=sentinel.user_svc,
            has_permission=has_permission,
        )

    @pytest.fixture
    def has_permission(self):
        return mock.Mock()

    @pytest.fixture
    def annotation_resource(self):
        return mock.Mock(spec_set=["annotation"], annotation=mock.Mock())

    @pytest.fixture
    def AnnotationContext(self, patch):
        return patch(
            "h.services.annotation_json_presentation.service.AnnotationContext"
        )

    @pytest.fixture(autouse=True)
    def formatters(self, patch):
        return patch("h.services.annotation_json_presentation.service.formatters")

    @pytest.fixture(autouse=True)
    def AnnotationJSONPresenter(self, patch):
        return patch(
            "h.services.annotation_json_presentation.service.AnnotationJSONPresenter"
        )
