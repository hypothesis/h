from unittest.mock import sentinel

import pytest

from h.services.annotation_json_presentation import AnnotationJSONPresentationService


class TestAnnotationJSONPresentationService:
    def test_it_configures_formatters(
        self, svc, formatters, db_session, flag_service, moderation_service
    ):
        formatters.AnnotationFlagFormatter.assert_called_once_with(
            sentinel.flag_svc, sentinel.user
        )
        formatters.AnnotationHiddenFormatter.assert_called_once_with(
            sentinel.moderation_svc, sentinel.has_permission, sentinel.user
        )
        formatters.AnnotationModerationFormatter.assert_called_once_with(
            sentinel.flag_count_svc, sentinel.user, sentinel.has_permission
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

    def test_present(self, svc, AnnotationJSONPresenter, AnnotationContext):
        result = svc.present(AnnotationContext.return_value)

        AnnotationJSONPresenter.assert_called_once_with(
            AnnotationContext.return_value,
            links_service=svc.links_svc,
            formatters=svc.formatters,
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

        AnnotationContext.assert_called_once_with(annotation, svc.links_svc)
        AnnotationJSONPresenter.assert_called_once_with(
            AnnotationContext.return_value,
            links_service=svc.links_svc,
            formatters=svc.formatters,
        )
        assert result == [
            AnnotationJSONPresenter.return_value.asdict.return_value,
        ]

    @pytest.fixture
    def svc(self, db_session):
        return AnnotationJSONPresentationService(
            session=db_session,
            user=sentinel.user,
            links_svc=sentinel.links_svc,
            flag_svc=sentinel.flag_svc,
            flag_count_svc=sentinel.flag_count_svc,
            moderation_svc=sentinel.moderation_svc,
            user_svc=sentinel.user_svc,
            has_permission=sentinel.has_permission,
        )

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
