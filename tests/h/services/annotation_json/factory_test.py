from unittest import mock
from unittest.mock import sentinel

import pytest

from h.services.annotation_json import annotation_json_service_factory


class TestAnnotationJSONServiceFactory:
    def test_it(
        self,
        pyramid_request,
        AnnotationJSONService,
        flag_service,
        links_service,
        user_service,
    ):
        service = annotation_json_service_factory(sentinel.context, pyramid_request)

        assert service == AnnotationJSONService.return_value

        AnnotationJSONService.assert_called_once_with(
            session=pyramid_request.db,
            links_service=links_service,
            flag_service=flag_service,
            user_service=user_service,
        )

    @pytest.fixture
    def AnnotationJSONService(self, patch):
        return patch("h.services.annotation_json.factory.AnnotationJSONService")

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.user = mock.Mock()
        return pyramid_request
