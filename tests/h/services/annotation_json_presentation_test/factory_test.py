from unittest import mock

import pytest

from h.services.annotation_json_presentation import (
    AnnotationJSONPresentationService,
    annotation_json_presentation_service_factory,
)


@pytest.mark.usefixtures("services")
class TestAnnotationJSONPresentationServiceFactory:
    def test_returns_service(self, pyramid_request):
        svc = annotation_json_presentation_service_factory(None, pyramid_request)

        assert isinstance(svc, AnnotationJSONPresentationService)

    def test_provides_session(self, pyramid_request, service_class):
        annotation_json_presentation_service_factory(None, pyramid_request)

        _, kwargs = service_class.call_args
        assert kwargs["session"] == pyramid_request.db

    def test_provides_user(self, pyramid_request, service_class):
        annotation_json_presentation_service_factory(None, pyramid_request)

        _, kwargs = service_class.call_args
        assert kwargs["user"] == pyramid_request.user

    def test_provides_group_service(self, pyramid_request, service_class, services):
        annotation_json_presentation_service_factory(None, pyramid_request)

        _, kwargs = service_class.call_args
        assert kwargs["group_svc"] == services["group"]

    def test_provides_links_service(self, pyramid_request, service_class, services):
        annotation_json_presentation_service_factory(None, pyramid_request)

        _, kwargs = service_class.call_args
        assert kwargs["links_svc"] == services["links"]

    def test_provides_flag_service(self, pyramid_request, service_class, services):
        annotation_json_presentation_service_factory(None, pyramid_request)

        _, kwargs = service_class.call_args
        assert kwargs["flag_svc"] == services["flag"]

    def test_provides_moderation_service(
        self, pyramid_request, service_class, services
    ):
        annotation_json_presentation_service_factory(None, pyramid_request)

        _, kwargs = service_class.call_args
        assert kwargs["moderation_svc"] == services["annotation_moderation"]

    def test_provides_flag_count_service(
        self, pyramid_request, service_class, services
    ):
        annotation_json_presentation_service_factory(None, pyramid_request)

        _, kwargs = service_class.call_args
        assert kwargs["flag_count_svc"] == services["flag_count"]

    def test_provides_has_permission(self, pyramid_request, service_class):
        annotation_json_presentation_service_factory(None, pyramid_request)

        _, kwargs = service_class.call_args
        assert kwargs["has_permission"] == pyramid_request.has_permission

    @pytest.fixture
    def service_class(self, patch):
        return patch(
            "h.services.annotation_json_presentation.factory.AnnotationJSONPresentationService"
        )

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.user = mock.Mock()
        return pyramid_request


@pytest.fixture
def services(pyramid_config, user_service, links_service, groupfinder_service):
    service_mocks = {
        "user": user_service,
        "links": links_service,
        "group": groupfinder_service,
    }

    for name in ["flag", "flag_count", "annotation_moderation"]:
        svc = mock.Mock()
        service_mocks[name] = svc
        pyramid_config.register_service(svc, name=name)

    return service_mocks
