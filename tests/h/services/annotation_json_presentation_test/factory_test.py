from unittest import mock
from unittest.mock import sentinel

import pytest

from h.services.annotation_json_presentation import (
    annotation_json_presentation_service_factory,
)


class TestAnnotationJSONPresentationServiceFactory:
    def test_it(
        self,
        pyramid_request,
        AnnotationJSONPresentationService,
        flag_service,
        flag_count_service,
        groupfinder_service,
        links_service,
        moderation_service,
        user_service,
    ):
        service = annotation_json_presentation_service_factory(
            sentinel.context, pyramid_request
        )

        assert service == AnnotationJSONPresentationService.return_value

        AnnotationJSONPresentationService.assert_called_once_with(
            session=pyramid_request.db,
            user=pyramid_request.user,
            has_permission=pyramid_request.has_permission,
            group_svc=groupfinder_service,
            links_svc=links_service,
            flag_svc=flag_service,
            flag_count_svc=flag_count_service,
            moderation_svc=moderation_service,
            user_svc=user_service,
        )

    @pytest.fixture
    def AnnotationJSONPresentationService(self, patch):
        return patch(
            "h.services.annotation_json_presentation.factory.AnnotationJSONPresentationService"
        )

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.user = mock.Mock()
        return pyramid_request
