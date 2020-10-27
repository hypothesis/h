from unittest.mock import create_autospec

import pytest

from h.services import search_index as search_index_
from h.services.annotation_moderation import AnnotationModerationService
from h.services.groupfinder import GroupfinderService
from h.services.links import LinksService
from h.services.nipsa import NipsaService

__all__ = (
    "mock_service",
    "search_index",
    "search_index_queue",
    "nipsa_service",
    "user_service",
    "links_service",
    "groupfinder_service",
    "moderation_service",
)

from h.services.user import UserService


@pytest.fixture
def mock_service(pyramid_config):
    def mock_service(service_class, name, spec_set=True, **kwargs):
        service = create_autospec(
            service_class, instance=True, spec_set=spec_set, **kwargs
        )
        pyramid_config.register_service(service, name=name)

        return service

    return mock_service


@pytest.fixture
def search_index(mock_service):
    return mock_service(
        search_index_.SearchIndexService, "search_index", spec_set=False
    )


@pytest.fixture
def search_index_queue(mock_service):
    return mock_service(search_index_.Queue, "search_index.queue", spec_set=False)


@pytest.fixture
def nipsa_service(mock_service):
    nipsa_service = mock_service(NipsaService, name="nipsa")
    nipsa_service.is_flagged.return_value = False

    return nipsa_service


@pytest.fixture
def user_service(mock_service):
    return mock_service(UserService, name="user")


@pytest.fixture
def links_service(mock_service):
    return mock_service(LinksService, name="links")


@pytest.fixture
def groupfinder_service(pyramid_config):
    service = create_autospec(GroupfinderService, instance=True, spec_set=True)
    pyramid_config.register_service(service, iface="h.interfaces.IGroupService")

    return service


@pytest.fixture
def moderation_service(mock_service):
    return mock_service(AnnotationModerationService, name="annotation_moderation")
