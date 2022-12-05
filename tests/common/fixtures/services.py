from unittest.mock import create_autospec

import pytest

from h.services.annotation_delete import AnnotationDeleteService
from h.services.annotation_json import AnnotationJSONService
from h.services.annotation_moderation import AnnotationModerationService
from h.services.auth_cookie import AuthCookieService
from h.services.auth_token import AuthTokenService
from h.services.delete_group import DeleteGroupService
from h.services.flag import FlagService
from h.services.group import GroupService
from h.services.group_create import GroupCreateService
from h.services.group_links import GroupLinksService
from h.services.group_list import GroupListService
from h.services.group_members import GroupMembersService
from h.services.group_update import GroupUpdateService
from h.services.links import LinksService
from h.services.list_organizations import ListOrganizationsService
from h.services.nipsa import NipsaService
from h.services.oauth.service import OAuthProviderService
from h.services.organization import OrganizationService
from h.services.search_index import SearchIndexService
from h.services.search_index._queue import Queue
from h.services.subscription import SubscriptionService
from h.services.user import UserService
from h.services.user_password import UserPasswordService
from h.services.user_signup import UserSignupService
from h.services.user_unique import UserUniqueService
from h.services.user_update import UserUpdateService

__all__ = (
    "mock_service",
    "annotation_delete_service",
    "annotation_json_service",
    "auth_cookie_service",
    "auth_token_service",
    "delete_group_service",
    "links_service",
    "list_organizations_service",
    "flag_service",
    "group_create_service",
    "group_links_service",
    "group_list_service",
    "group_members_service",
    "group_service",
    "group_update_service",
    "nipsa_service",
    "moderation_service",
    "oauth_provider_service",
    "organization_service",
    "search_index",
    "subscription_service",
    "user_password_service",
    "user_service",
    "user_password_service",
    "user_signup_service",
    "user_unique_service",
    "user_update_service",
)


@pytest.fixture
def mock_service(pyramid_config):
    def mock_service(service_class, name=None, iface=None, spec_set=True, **kwargs):
        service = create_autospec(
            service_class, instance=True, spec_set=spec_set, **kwargs
        )
        if name:
            pyramid_config.register_service(service, name=name)
        else:
            pyramid_config.register_service(service, iface=iface or service_class)

        return service

    return mock_service


@pytest.fixture
def annotation_delete_service(mock_service):
    return mock_service(AnnotationDeleteService, name="annotation_delete")


@pytest.fixture
def annotation_json_service(mock_service):
    return mock_service(AnnotationJSONService, name="annotation_json")


@pytest.fixture
def auth_cookie_service(mock_service):
    return mock_service(AuthCookieService)


@pytest.fixture
def auth_token_service(mock_service):
    return mock_service(AuthTokenService, name="auth_token")


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
def flag_service(pyramid_config):
    service = create_autospec(FlagService, instance=True, spec_set=True)
    pyramid_config.register_service(service, name="flag")

    return service


@pytest.fixture
def group_create_service(mock_service):
    return mock_service(GroupCreateService, name="group_create")


@pytest.fixture
def group_links_service(mock_service):
    return mock_service(GroupLinksService, name="group_links")


@pytest.fixture
def group_list_service(mock_service):
    return mock_service(GroupListService, name="group_list")


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
def oauth_provider_service(mock_service):
    return mock_service(OAuthProviderService, name="oauth_provider")


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
def subscription_service(mock_service):
    return mock_service(SubscriptionService)


@pytest.fixture
def user_password_service(mock_service):
    return mock_service(UserPasswordService, name="user_password")


@pytest.fixture
def user_service(mock_service):
    return mock_service(UserService, name="user")


@pytest.fixture
def user_signup_service(mock_service):
    return mock_service(UserSignupService, name="user_signup")


@pytest.fixture
def user_unique_service(mock_service):
    return mock_service(UserUniqueService, name="user_unique")


@pytest.fixture
def user_update_service(mock_service):
    return mock_service(UserUpdateService, name="user_update")
