from unittest.mock import create_autospec

import pytest

from h.services.annotation_delete import AnnotationDeleteService
from h.services.annotation_moderation import AnnotationModerationService
from h.services.delete_group import DeleteGroupService
from h.services.group import GroupService
from h.services.group_create import GroupCreateService
from h.services.group_members import GroupMembersService
from h.services.group_update import GroupUpdateService
from h.services.groupfinder import GroupfinderService
from h.services.links import LinksService
from h.services.list_organizations import ListOrganizationsService
from h.services.nipsa import NipsaService
from h.services.organization import OrganizationService
from h.services.search_index import SearchIndexService
from h.services.search_index._queue import Queue

__all__ = (
    "mock_service",
    "annotation_delete_service",
    "delete_group_service",
    "links_service",
    "list_organizations_service",
    "groupfinder_service",
    "group_create_service",
    "group_members_service",
    "group_service",
    "group_update_service",
    "nipsa_service",
    "moderation_service",
    "organization_service",
    "search_index",
    "user_service",
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
def annotation_delete_service(mock_service):
    return mock_service(AnnotationDeleteService, name="annotation_delete")


@pytest.fixture
def delete_group_service(mock_service):
    return mock_service(DeleteGroupService, name="delete_group")


@pytest.fixture
def links_service(mock_service):
    return mock_service(LinksService, name="links")


@pytest.fixture
def list_organizations_service(mock_service, default_organization):
    list_organizations_service = mock_service(
        ListOrganizationsService, name="list_organizations"
    )

    list_organizations_service.organizations.return_value = [default_organization]
    return list_organizations_service


@pytest.fixture
def groupfinder_service(pyramid_config):
    service = create_autospec(GroupfinderService, instance=True, spec_set=True)
    pyramid_config.register_service(service, iface="h.interfaces.IGroupService")

    return service


@pytest.fixture
def group_create_service(mock_service):
    return mock_service(GroupCreateService, name="group_create")


@pytest.fixture
def group_members_service(mock_service):
    return mock_service(GroupMembersService, name="group_members")


@pytest.fixture
def group_service(mock_service):
    return mock_service(GroupService, name="group")


@pytest.fixture
def group_update_service(mock_service):
    return mock_service(GroupUpdateService, name="group_update")


@pytest.fixture
def moderation_service(mock_service):
    return mock_service(AnnotationModerationService, name="annotation_moderation")


@pytest.fixture
def nipsa_service(mock_service):
    nipsa_service = mock_service(NipsaService, name="nipsa")
    nipsa_service.is_flagged.return_value = False

    return nipsa_service


@pytest.fixture
def organization_service(mock_service):
    return mock_service(OrganizationService, name="organization")


@pytest.fixture
def search_index(mock_service):
    return mock_service(
        SearchIndexService,
        "search_index",
        spec_set=False,
        _queue=create_autospec(Queue, spec_set=True, instance=True),
    )


@pytest.fixture
def user_service(mock_service):
    return mock_service(UserService, name="user")
