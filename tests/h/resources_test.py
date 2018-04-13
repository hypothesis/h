# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import mock

from pyramid import security
from pyramid.authorization import ACLAuthorizationPolicy

from h.models import AuthClient, Organization
from h.services.group_links import GroupLinksService
from h.resources import AnnotationResource
from h.resources import AnnotationResourceFactory
from h.resources import AuthClientFactory
from h.resources import OrganizationFactory
from h.resources import OrganizationLogoFactory
from h.resources import GroupResource
from h.resources import OrganizationResource


@pytest.mark.usefixtures('group_service', 'links_service')
class TestAnnotationResourceFactory(object):
    def test_get_item_fetches_annotation(self, pyramid_request, storage):
        factory = AnnotationResourceFactory(pyramid_request)

        factory['123']
        storage.fetch_annotation.assert_called_once_with(pyramid_request.db, '123')

    def test_get_item_returns_annotation_resource(self, pyramid_request, storage):
        factory = AnnotationResourceFactory(pyramid_request)
        storage.fetch_annotation.return_value = mock.Mock()

        resource = factory['123']
        assert isinstance(resource, AnnotationResource)

    def test_get_item_resource_has_right_annotation(self, pyramid_request, storage):
        factory = AnnotationResourceFactory(pyramid_request)
        storage.fetch_annotation.return_value = mock.Mock()

        resource = factory['123']
        assert resource.annotation == storage.fetch_annotation.return_value

    def test_get_item_raises_when_annotation_is_not_found(self, storage, pyramid_request):
        factory = AnnotationResourceFactory(pyramid_request)
        storage.fetch_annotation.return_value = None

        with pytest.raises(KeyError):
            factory['123']

    def test_get_item_has_right_group_service(self, pyramid_request, storage, group_service):
        factory = AnnotationResourceFactory(pyramid_request)
        storage.fetch_annotation.return_value = mock.Mock()

        resource = factory['123']
        assert resource.group_service == group_service

    def test_get_item_has_right_links_service(self, pyramid_request, storage, links_service):
        factory = AnnotationResourceFactory(pyramid_request)
        storage.fetch_annotation.return_value = mock.Mock()

        resource = factory['123']
        assert resource.links_service == links_service

    @pytest.fixture
    def storage(self, patch):
        return patch('h.resources.storage')

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


@pytest.mark.usefixtures('group_service', 'links_service')
class TestAnnotationResource(object):
    def test_links(self, group_service, links_service):
        ann = mock.Mock()
        res = AnnotationResource(ann, group_service, links_service)

        result = res.links

        links_service.get_all.assert_called_once_with(ann)
        assert result == links_service.get_all.return_value

    def test_link(self, group_service, links_service):
        ann = mock.Mock()
        res = AnnotationResource(ann, group_service, links_service)

        result = res.link('json')

        links_service.get.assert_called_once_with(ann, 'json')
        assert result == links_service.get.return_value

    def test_acl_private(self, factories, group_service, links_service):
        ann = factories.Annotation(shared=False, userid='saoirse')
        res = AnnotationResource(ann, group_service, links_service)
        actual = res.__acl__()
        expect = [(security.Allow, 'saoirse', 'read'),
                  (security.Allow, 'saoirse', 'admin'),
                  (security.Allow, 'saoirse', 'update'),
                  (security.Allow, 'saoirse', 'delete'),
                  security.DENY_ALL]
        assert actual == expect

    def test_acl_shared_admin_perms(self, factories, group_service, links_service):
        """
        Shared annotation resources should still only give admin/update/delete
        permissions to the owner.
        """
        policy = ACLAuthorizationPolicy()

        ann = factories.Annotation(shared=False, userid='saoirse')
        res = AnnotationResource(ann, group_service, links_service)

        for perm in ['admin', 'update', 'delete']:
            assert policy.permits(res, ['saoirse'], perm)
            assert not policy.permits(res, ['someoneelse'], perm)

    def test_acl_deleted(self, factories, group_service, links_service):
        """
        Nobody -- not even the owner -- should have any permissions on a
        deleted annotation.
        """
        policy = ACLAuthorizationPolicy()

        ann = factories.Annotation(userid='saoirse', deleted=True)
        res = AnnotationResource(ann, group_service, links_service)

        for perm in ['read', 'admin', 'update', 'delete']:
            assert not policy.permits(res, ['saiorse'], perm)

    @pytest.mark.parametrize('groupid,userid,permitted', [
        ('freeforall', 'jim', True),
        ('freeforall', 'saoirse', True),
        ('freeforall', None, True),
        ('only-saoirse', 'jim', False),
        ('only-saoirse', 'saoirse', True),
        ('only-saoirse', None, False),
        ('pals', 'jim', True),
        ('pals', 'saoirse', True),
        ('pals', 'francis', False),
        ('pals', None, False),
        ('unknown-group', 'jim', False),
        ('unknown-group', 'saoirse', False),
        ('unknown-group', 'francis', False),
        ('unknown-group', None, False),
    ])
    def test_acl_shared(self,
                        factories,
                        pyramid_config,
                        pyramid_request,
                        groupid,
                        userid,
                        permitted,
                        group_service,
                        links_service):
        """
        Shared annotation resources should delegate their 'read' permission to
        their containing group.
        """
        # Set up the test with a dummy authn policy and a real ACL authz
        # policy:
        policy = ACLAuthorizationPolicy()
        pyramid_config.testing_securitypolicy(userid)
        pyramid_config.set_authorization_policy(policy)

        ann = factories.Annotation(shared=True,
                                   userid='mioara',
                                   groupid=groupid)
        res = AnnotationResource(ann, group_service, links_service)

        if permitted:
            assert pyramid_request.has_permission('read', res)
        else:
            assert not pyramid_request.has_permission('read', res)

    @pytest.fixture
    def groups(self):
        return {
            'freeforall': FakeGroup([security.Everyone]),
            'only-saoirse': FakeGroup(['saoirse']),
            'pals': FakeGroup(['saoirse', 'jim']),
        }

    @pytest.fixture
    def group_service(self, pyramid_config, groups):
        group_service = mock.Mock(spec_set=['find'])
        group_service.find.side_effect = lambda groupid: groups.get(groupid)
        pyramid_config.register_service(group_service, iface='h.interfaces.IGroupService')
        return group_service

    @pytest.fixture
    def links_service(self, pyramid_config):
        service = mock.Mock(spec_set=['get', 'get_all'])
        pyramid_config.register_service(service, name='links')
        return service


class TestAuthClientResourceFactory(object):
    def test_get_item_returns_an_authclient(self, pyramid_request):
        authclient = AuthClient(name='test', authority='example.com')
        pyramid_request.db.add(authclient)
        pyramid_request.db.flush()

        factory = AuthClientFactory(pyramid_request)
        assert factory[authclient.id] == authclient

    def test_get_item_returns_keyerror_if_not_found(self, pyramid_request):
        factory = AuthClientFactory(pyramid_request)
        with pytest.raises(KeyError):
            factory['E19D247D-1F07-4E91-B40D-00DF22E693E4']

    def test_get_item_returns_keyerror_if_invalid(self, pyramid_request):
        factory = AuthClientFactory(pyramid_request)
        with pytest.raises(KeyError):
            factory['not-a-uuid']


@pytest.mark.usefixtures('organizations')
class TestOrganizationFactory(object):

    def test_it_returns_the_requested_organization(self, organizations, organization_factory):
        organization = organizations[1]

        assert organization_factory[organization.pubid] == organization

    def test_it_404s_if_the_organization_doesnt_exist(self, organization_factory):
        with pytest.raises(KeyError):
            organization_factory['does_not_exist']

    @pytest.fixture
    def organization_factory(self, pyramid_request):
        return OrganizationFactory(pyramid_request)


@pytest.mark.usefixtures('organizations')
class TestOrganizationLogoFactory(object):

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
        return OrganizationLogoFactory(pyramid_request)


@pytest.mark.usefixtures('links_svc')
class TestGroupResource(object):

    def test_it_returns_group_model_as_property(self, factories, pyramid_request):
        group = factories.Group()

        group_resource = GroupResource(group, pyramid_request)

        assert group_resource.group == group

    def test_it_proxies_links_to_svc(self, factories, links_svc, pyramid_request):
        group = factories.Group()

        group_resource = GroupResource(group, pyramid_request)

        assert group_resource.links == links_svc.get_all.return_value

    def test_it_returns_pubid_as_id(self, factories, pyramid_request):
        group = factories.Group()

        group_resource = GroupResource(group, pyramid_request)

        assert group_resource.id == group.pubid  # NOT the group.id

    def test_it_expands_organization(self, factories, pyramid_request):
        group = factories.Group()

        group_resource = GroupResource(group, pyramid_request)

        assert isinstance(group_resource.organization, OrganizationResource)


@pytest.mark.usefixtures('organization_routes')
class TestOrganizationResource(object):

    def test_it_returns_organization_model_as_property(self, factories, pyramid_request):
        organization = factories.Organization()

        organization_resource = OrganizationResource(organization, pyramid_request)

        assert organization_resource.organization == organization

    def test_it_returns_pubid_as_id(self, factories, pyramid_request):
        organization = factories.Organization()

        organization_resource = OrganizationResource(organization, pyramid_request)

        assert organization_resource.id != organization.id
        assert organization_resource.id == organization.pubid

    def test_it_returns_links_property(self, factories, pyramid_request):
        organization = factories.Organization()

        organization_resource = OrganizationResource(organization, pyramid_request)

        assert organization_resource.links == {}

    def test_it_returns_logo_property_as_route_url(self, factories, pyramid_request):
        fake_logo = '<svg>H</svg>'
        pyramid_request.route_url = mock.Mock()

        organization = factories.Organization(logo=fake_logo)

        organization_resource = OrganizationResource(organization, pyramid_request)
        logo = organization_resource.logo

        pyramid_request.route_url.assert_called_with('organization_logo', pubid=organization.pubid)
        assert logo is not None

    def test_it_returns_none_for_logo_if_no_logo(self, factories, pyramid_request):
        pyramid_request.route_url = mock.Mock()

        organization = factories.Organization(logo=None)

        organization_resource = OrganizationResource(organization, pyramid_request)
        logo = organization_resource.logo

        pyramid_request.route_url.assert_not_called
        assert logo is None

    def test_default_property_if_not_default_organization(self, factories, pyramid_request):
        organization = factories.Organization()

        organization_resource = OrganizationResource(organization, pyramid_request)

        assert organization_resource.default is False

    def test_default_property_if_default_organization(self, factories, pyramid_request):
        organization = Organization.default(pyramid_request.db)

        organization_resource = OrganizationResource(organization, pyramid_request)

        assert organization_resource.default is True


@pytest.fixture
def organizations(factories):
    # Add a handful of organizations to the DB to make the test realistic.
    return [factories.Organization() for _ in range(3)]


@pytest.fixture
def links_svc(pyramid_config):
    svc = mock.create_autospec(GroupLinksService, spec_set=True, instance=True)
    pyramid_config.register_service(svc, name='group_links')
    return svc


@pytest.fixture
def organization_routes(pyramid_config):
    pyramid_config.add_route('organization_logo', '/organization/{pubid}/logo')


class FakeGroup(object):
    def __init__(self, principals):
        self.__acl__ = [(security.Allow, p, 'read') for p in principals]
