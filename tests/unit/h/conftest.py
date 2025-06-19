import functools
import os
from unittest import mock
from unittest.mock import create_autospec

import click.testing
import deform
import pytest
from pyramid import testing
from pyramid.request import apply_request_extensions
from webob.multidict import MultiDict

from h.models import Organization
from h.models.auth_client import GrantType
from h.security import Identity
from h.services import (
    HTTPService,
    MentionService,
    NotificationService,
    OpenIDClientService,
    ORCIDClientService,
)
from h.services.analytics import AnalyticsService
from h.services.annotation_authority_queue import AnnotationAuthorityQueueService
from h.services.annotation_delete import AnnotationDeleteService
from h.services.annotation_json import AnnotationJSONService
from h.services.annotation_metadata import AnnotationMetadataService
from h.services.annotation_moderation import AnnotationModerationService
from h.services.annotation_read import AnnotationReadService
from h.services.annotation_stats import AnnotationStatsService
from h.services.annotation_sync import AnnotationSyncService
from h.services.annotation_write import AnnotationWriteService
from h.services.auth_ticket import AuthTicketService
from h.services.auth_token import AuthTokenService
from h.services.bulk_api import (
    BulkAnnotationService,
    BulkGroupService,
    BulkLMSStatsService,
)
from h.services.developer_token import DeveloperTokenService
from h.services.email import EmailService
from h.services.feature import FeatureService
from h.services.flag import FlagService
from h.services.group import GroupService
from h.services.group_create import GroupCreateService
from h.services.group_delete import GroupDeleteService
from h.services.group_links import GroupLinksService
from h.services.group_list import GroupListService
from h.services.group_members import GroupMembersService
from h.services.group_update import GroupUpdateService
from h.services.job_queue import JobQueueService
from h.services.links import LinksService
from h.services.list_organizations import ListOrganizationsService
from h.services.nipsa import NipsaService
from h.services.oauth.service import OAuthProviderService
from h.services.organization import OrganizationService
from h.services.search_index import SearchIndexService
from h.services.subscription import SubscriptionService
from h.services.task_done import TaskDoneService
from h.services.url_migration import URLMigrationService
from h.services.user import UserService
from h.services.user_delete import UserDeleteService
from h.services.user_password import UserPasswordService
from h.services.user_signup import UserSignupService
from h.services.user_unique import UserUniqueService
from h.services.user_update import UserUpdateService
from tests.common import factories as common_factories


class DummyFeature:
    """
    A dummy feature flag looker-upper.

    Because we're probably testing all feature-flagged functionality, this
    feature client defaults every flag to *True*, which is the exact opposite
    of what happens outside of testing.
    """

    def __init__(self):
        self.flags = {}
        self.loaded = False

    def __call__(self, name, *args, **kwargs):  # noqa: ARG002
        return self.flags.get(name, True)

    def all(self):
        return self.flags


# A fake version of colander.Invalid
class FakeInvalid:
    def __init__(self, errors):
        self.errors = errors

    def asdict(self):
        return self.errors


@pytest.fixture
def cli():
    runner = click.testing.CliRunner()
    with runner.isolated_filesystem():
        yield runner


@pytest.fixture
def default_organization(db_session):
    # This looks a bit odd, but as part of our DB initialization we always add
    # a default org. So tests can't add their own without causing a conflict.
    return (
        db_session.query(Organization).filter_by(pubid=Organization.DEFAULT_PUBID).one()
    )


@pytest.fixture
def factories(db_session):
    common_factories.set_session(db_session)
    yield common_factories
    common_factories.set_session(None)


@pytest.fixture
def fake_feature():
    return DummyFeature()


@pytest.fixture
def form_validating_to():
    def form_validating_to(appstruct):
        form = mock.MagicMock()
        form.validate.return_value = appstruct
        form.render.return_value = "valid form"
        return form

    return form_validating_to


@pytest.fixture
def invalid_form():
    def invalid_form(errors=None):
        invalid = FakeInvalid(errors or {})
        form = mock.MagicMock()
        form.validate.side_effect = deform.ValidationFailure(None, None, invalid)
        form.render.return_value = "invalid form"
        return form

    return invalid_form


@pytest.fixture
def matchers():
    from tests.common import matchers

    return matchers


@pytest.fixture
def notify(pyramid_config, request):
    patcher = mock.patch.object(pyramid_config.registry, "notify", autospec=True)
    request.addfinalizer(patcher.stop)  # noqa: PT021
    return patcher.start()


@pytest.fixture
def patch(mocker):
    return functools.partial(mocker.patch, autospec=True)


@pytest.fixture
def pyramid_config(pyramid_settings, pyramid_request):
    """Return Pyramid configurator object."""
    with testing.testConfig(
        request=pyramid_request, settings=pyramid_settings
    ) as config:
        # Include pyramid_services so it's easy to set up fake services in tests
        config.include("pyramid_services")
        config.include("h.security.request_methods")
        apply_request_extensions(pyramid_request)

        yield config


@pytest.fixture
def pyramid_request(db_session, db_session_replica, fake_feature, pyramid_settings):
    """Return pyramid request object."""
    request = testing.DummyRequest(
        db=db_session, db_replica=db_session_replica, feature=fake_feature
    )
    request.default_authority = "example.com"
    request.create_form = mock.Mock()

    request.matched_route = mock.Mock(spec=["name"])
    # `name` is a special argument to the Mock constructor so if you want a
    # mock to have a `name` attribute you can't just do Mock(name="name"), you
    # have to use a separate call to configure_mock() instead.
    # https://docs.python.org/3/library/unittest.mock.html#mock-names-and-the-name-attribute
    request.matched_route.configure_mock(name="index")

    request.registry.settings = pyramid_settings
    request.is_xhr = False
    request.params = MultiDict()
    request.GET = request.params
    request.POST = request.params
    request.user = None
    request.scheme = "https"
    return request


@pytest.fixture
def pyramid_csrf_request(pyramid_request):
    """Return a dummy Pyramid request object with a valid CSRF token."""
    pyramid_request.headers["X-CSRF-Token"] = pyramid_request.session.get_csrf_token()
    pyramid_request.referrer = "https://example.com"
    pyramid_request.host_port = "80"
    return pyramid_request


@pytest.fixture
def pyramid_settings():
    """Return the default app settings."""
    return {"sqlalchemy.url": os.environ["DATABASE_URL"]}


@pytest.fixture
def auth_client(factories):
    return factories.ConfidentialAuthClient(grant_type=GrantType.client_credentials)


@pytest.fixture
def with_auth_client(auth_client, pyramid_config):
    pyramid_config.testing_securitypolicy(
        identity=Identity.from_models(auth_client=auth_client)
    )


@pytest.fixture
def mock_service(pyramid_config):
    def mock_service(service_class, name=None, iface=None, spec_set=True, **kwargs):  # noqa: FBT002
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
def analytics_service(mock_service):
    return mock_service(AnalyticsService, name="analytics")


@pytest.fixture
def annotation_delete_service(mock_service):
    return mock_service(AnnotationDeleteService, name="annotation_delete")


@pytest.fixture
def annotation_json_service(mock_service):
    return mock_service(AnnotationJSONService, name="annotation_json")


@pytest.fixture
def annotation_stats_service(mock_service):
    return mock_service(AnnotationStatsService, name="annotation_stats")


@pytest.fixture
def annotation_read_service(mock_service):
    return mock_service(AnnotationReadService)


@pytest.fixture
def annotation_sync_service(mock_service):
    return mock_service(AnnotationSyncService)


@pytest.fixture
def annotation_write_service(mock_service):
    return mock_service(AnnotationWriteService)


@pytest.fixture
def annotation_metadata_service(mock_service):
    return mock_service(AnnotationMetadataService)


@pytest.fixture
def auth_ticket_service(mock_service):
    auth_ticket_service = mock_service(AuthTicketService)
    auth_ticket_service.verify_ticket.return_value.deleted = False
    return auth_ticket_service


@pytest.fixture
def auth_token_service(mock_service):
    return mock_service(AuthTokenService, name="auth_token")


@pytest.fixture
def bulk_annotation_service(mock_service):
    return mock_service(BulkAnnotationService)


@pytest.fixture
def bulk_group_service(mock_service):
    return mock_service(BulkGroupService)


@pytest.fixture
def bulk_stats_service(mock_service):
    return mock_service(BulkLMSStatsService)


@pytest.fixture
def developer_token_service(mock_service):
    return mock_service(DeveloperTokenService, name="developer_token")


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
def group_delete_service(mock_service):
    return mock_service(GroupDeleteService, name="group_delete")


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
    return mock_service(SearchIndexService, "search_index", spec_set=False)


@pytest.fixture
def queue_service(mock_service):
    return mock_service(JobQueueService, name="queue_service")


@pytest.fixture
def subscription_service(mock_service):
    return mock_service(SubscriptionService)


@pytest.fixture
def url_migration_service(mock_service):
    return mock_service(URLMigrationService, name="url_migration")


@pytest.fixture
def user_delete_service(mock_service):
    return mock_service(UserDeleteService, name="user_delete")


@pytest.fixture
def user_password_service(mock_service):
    return mock_service(UserPasswordService, name="user_password")


@pytest.fixture
def user_service(mock_service):
    user_service = mock_service(UserService, name="user")
    user_service.fetch.return_value.deleted = False
    return user_service


@pytest.fixture
def user_signup_service(mock_service):
    return mock_service(UserSignupService, name="user_signup")


@pytest.fixture
def user_unique_service(mock_service):
    return mock_service(UserUniqueService, name="user_unique")


@pytest.fixture
def user_update_service(mock_service):
    return mock_service(UserUpdateService, name="user_update")


@pytest.fixture
def mention_service(mock_service):
    return mock_service(MentionService)


@pytest.fixture
def notification_service(mock_service):
    return mock_service(NotificationService)


@pytest.fixture
def annotation_authority_queue_service(mock_service):
    return mock_service(AnnotationAuthorityQueueService)


@pytest.fixture
def feature_service(mock_service):
    return mock_service(FeatureService, name="feature")


@pytest.fixture
def email_service(mock_service):
    return mock_service(EmailService)


@pytest.fixture
def task_done_service(mock_service):
    return mock_service(TaskDoneService)


@pytest.fixture
def http_service(mock_service):
    return mock_service(HTTPService)


@pytest.fixture
def openid_client_service(mock_service):
    return mock_service(OpenIDClientService)


@pytest.fixture
def orcid_client_service(mock_service):
    return mock_service(ORCIDClientService)
