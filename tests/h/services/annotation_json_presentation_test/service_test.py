from unittest import mock
from unittest.mock import sentinel

import pytest
from h_matchers import Any

from h.security.permissions import Permission
from h.services.annotation_json_presentation import AnnotationJSONPresentationService


@pytest.mark.usefixtures("presenters", "formatters")
class TestAnnotationJSONPresentationService:
    def test_it_configures_formatters(
        self, svc, formatters, flag_service, moderation_service, has_permission
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
            sentinel.db_session, sentinel.user_svc
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

    def test_present_calls_presenter(self, svc, presenters, annotation_resource):
        result = svc.present(annotation_resource)

        presenters.AnnotationJSONPresenter.assert_called_once_with(
            annotation_resource, svc.formatters
        )

        assert (
            result
            == presenters.AnnotationJSONPresenter.return_value.asdict.return_value
        )

    def test_present_all_loads_annotations_from_db(self, svc, storage):
        svc.present_all(["id-1", "id-2"])

        storage.fetch_ordered_annotations.assert_called_once_with(
            svc.session, ["id-1", "id-2"], query_processor=Any()
        )

    def test_present_all_initialises_annotation_resources(
        self, svc, storage, traversal
    ):
        ann = mock.Mock()
        storage.fetch_ordered_annotations.return_value = [ann]

        svc.present_all(["ann-1"])

        traversal.AnnotationContext.assert_called_once_with(
            ann, svc.group_svc, svc.links_svc
        )

    def test_present_all_presents_annotation_resources(
        self, svc, storage, traversal, present
    ):
        storage.fetch_ordered_annotations.return_value = [mock.Mock()]
        resource = traversal.AnnotationContext.return_value

        svc.present_all(["ann-1"])
        present.assert_called_once_with(svc, resource)

    def test_present_all_preloads_formatters(self, svc, storage):
        formatter = mock.Mock(spec_set=["preload"])
        svc.formatters = [formatter]

        svc.present_all(["ann-1", "ann-2"])

        formatter.preload.assert_called_once_with(["ann-1", "ann-2"])

    def test_returns_presented_annotations(self, svc, storage, present):
        storage.fetch_ordered_annotations.return_value = [mock.Mock()]

        result = svc.present_all(["ann-1"])
        assert result == [present.return_value]

    @pytest.fixture
    def svc(self, has_permission):
        return AnnotationJSONPresentationService(
            session=sentinel.db_session,
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
    def presenters(self, patch):
        return patch("h.services.annotation_json_presentation.service.presenters")

    @pytest.fixture
    def storage(self, patch):
        return patch("h.services.annotation_json_presentation.service.storage")

    @pytest.fixture
    def traversal(self, patch):
        return patch("h.services.annotation_json_presentation.service.traversal")

    @pytest.fixture
    def present(self, patch):
        return patch(
            "h.services.annotation_json_presentation.service.AnnotationJSONPresentationService.present"
        )

    @pytest.fixture
    def formatters(self, patch):
        return patch("h.services.annotation_json_presentation.service.formatters")
