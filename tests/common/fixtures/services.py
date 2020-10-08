from unittest.mock import create_autospec

import pytest

from h.services.annotation_moderation import AnnotationModerationService
from h.services.nipsa import NipsaService
from h.services.search_index import SearchIndexService

__all__ = ("mock_service", "search_index", "nipsa_service", "moderation_service")


@pytest.fixture
def mock_service(pyramid_config):
    def mock_service(service_class, name):
        service = create_autospec(service_class, instance=True, spec_set=True)
        pyramid_config.register_service(service, name=name)

        return service

    return mock_service


@pytest.fixture
def search_index(mock_service):
    return mock_service(SearchIndexService, "search_index")


@pytest.fixture
def nipsa_service(mock_service):
    nipsa_service = mock_service(NipsaService, name="nipsa")
    nipsa_service.is_flagged.return_value = False

    return nipsa_service


@pytest.fixture
def moderation_service(mock_service):
    return mock_service(AnnotationModerationService, name="annotation_moderation")
