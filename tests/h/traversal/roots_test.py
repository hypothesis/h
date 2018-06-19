# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import mock

from h.models import AuthClient
from h.services.user import UserService
from h.traversal.roots import AnnotationRoot
from h.traversal.roots import AuthClientRoot
from h.traversal.roots import OrganizationRoot
from h.traversal.roots import OrganizationLogoRoot
from h.traversal.roots import GroupRoot
from h.traversal.roots import UserRoot
from h.traversal.contexts import AnnotationContext


@pytest.mark.usefixtures('group_service', 'links_service')
class TestAnnotationRoot(object):
    def test_get_item_fetches_annotation(self, pyramid_request, storage):
        factory = AnnotationRoot(pyramid_request)

        factory['123']
        storage.fetch_annotation.assert_called_once_with(pyramid_request.db, '123')

    def test_get_item_returns_annotation_resource(self, pyramid_request, storage):
        factory = AnnotationRoot(pyramid_request)
        storage.fetch_annotation.return_value = mock.Mock()

        resource = factory['123']
        assert isinstance(resource, AnnotationContext)

    def test_get_item_resource_has_right_annotation(self, pyramid_request, storage):
        factory = AnnotationRoot(pyramid_request)
        storage.fetch_annotation.return_value = mock.Mock()

        resource = factory['123']
        assert resource.annotation == storage.fetch_annotation.return_value

    def test_get_item_raises_when_annotation_is_not_found(self, storage, pyramid_request):
        factory = AnnotationRoot(pyramid_request)
        storage.fetch_annotation.return_value = None

        with pytest.raises(KeyError):
            factory['123']

    def test_get_item_has_right_group_service(self, pyramid_request, storage, group_service):
        factory = AnnotationRoot(pyramid_request)
        storage.fetch_annotation.return_value = mock.Mock()

        resource = factory['123']
        assert resource.group_service == group_service

    def test_get_item_has_right_links_service(self, pyramid_request, storage, links_service):
        factory = AnnotationRoot(pyramid_request)
        storage.fetch_annotation.return_value = mock.Mock()

        resource = factory['123']
        assert resource.links_service == links_service

    @pytest.fixture
    def storage(self, patch):
        return patch('h.traversal.roots.storage')

    @pytest.fixture
    def group_service(self, pyramid_config):
        group_service = mock.Mock(spec_set=['find'])
        pyramid_config.register_service(group_service, iface='h.interfaces.IGroupService')
        return group_service

    @pytest.fixture
    def links_service(self, pyramid_config):
        service = mock.Mock()
        pyramid_config.register_service(service, name='links')
        return service


class TestAuthClientRoot(object):
    def test_get_item_returns_an_authclient(self, pyramid_request):
        authclient = AuthClient(name='test', authority='example.com')
        pyramid_request.db.add(authclient)
        pyramid_request.db.flush()

        factory = AuthClientRoot(pyramid_request)
        assert factory[authclient.id] == authclient

    def test_get_item_returns_keyerror_if_not_found(self, pyramid_request):
        factory = AuthClientRoot(pyramid_request)
        with pytest.raises(KeyError):
            factory['E19D247D-1F07-4E91-B40D-00DF22E693E4']

    def test_get_item_returns_keyerror_if_invalid(self, pyramid_request):
        factory = AuthClientRoot(pyramid_request)
        with pytest.raises(KeyError):
            factory['not-a-uuid']


@pytest.mark.usefixtures('organizations')
class TestOrganizationRoot(object):

    def test_it_returns_the_requested_organization(self, organizations, organization_factory):
        organization = organizations[1]

        assert organization_factory[organization.pubid] == organization

    def test_it_404s_if_the_organization_doesnt_exist(self, organization_factory):
        with pytest.raises(KeyError):
            organization_factory['does_not_exist']

    @pytest.fixture
    def organization_factory(self, pyramid_request):
        return OrganizationRoot(pyramid_request)


@pytest.mark.usefixtures('organizations')
class TestOrganizationLogoRoot(object):

    def test_it_returns_the_requested_organizations_logo(self, organizations, organization_logo_factory):
        organization = organizations[1]
        organization.logo = '<svg>blah</svg>'

        assert organization_logo_factory[organization.pubid] == '<svg>blah</svg>'

    def test_it_404s_if_the_organization_doesnt_exist(self, organization_logo_factory):
        with pytest.raises(KeyError):
            organization_logo_factory['does_not_exist']

    def test_it_404s_if_the_organization_has_no_logo(self, organizations, organization_logo_factory):
        with pytest.raises(KeyError):
            assert organization_logo_factory[organizations[0].pubid]

    @pytest.fixture
    def organization_logo_factory(self, pyramid_request):
        return OrganizationLogoRoot(pyramid_request)


@pytest.mark.usefixtures("groups")
class TestGroupRoot(object):

    def test_it_returns_the_group_if_it_exists(self, factories, group_factory):
        group = factories.Group()

        assert group_factory[group.pubid] == group

    def test_it_raises_KeyError_if_the_group_doesnt_exist(self, group_factory):
        with pytest.raises(KeyError):
            group_factory["does_not_exist"]

    @pytest.fixture
    def groups(self, factories):
        # Add some "noise" groups to the DB.
        # These are groups that we _don't_ expect GroupRoot to return in
        # the tests.
        return [factories.Group(), factories.Group(), factories.Group()]

    @pytest.fixture
    def group_factory(self, pyramid_request):
        return GroupRoot(pyramid_request)


@pytest.mark.usefixtures('user_service')
class TestUserRoot(object):

    def test_it_fetches_the_requested_user(self, pyramid_request, user_factory, user_service):
        user_factory["bob"]

        user_service.fetch.assert_called_once_with("bob", pyramid_request.authority)

    def test_it_raises_KeyError_if_the_user_does_not_exist(self,
                                                           user_factory,
                                                           user_service):
        user_service.fetch.return_value = None

        with pytest.raises(KeyError):
            user_factory["does_not_exist"]

    def test_it_returns_users(self, factories, user_factory, user_service):
        user_service.fetch.return_value = user = factories.User.build()

        assert user_factory[user.username] == user

    @pytest.fixture
    def user_factory(self, pyramid_request):
        return UserRoot(pyramid_request)

    @pytest.fixture
    def user_service(self, pyramid_config):
        user_service = mock.create_autospec(UserService, spec_set=True, instance=True)
        pyramid_config.register_service(user_service, name='user')
        return user_service


@pytest.fixture
def organizations(factories):
    # Add a handful of organizations to the DB to make the test realistic.
    return [factories.Organization() for _ in range(3)]
