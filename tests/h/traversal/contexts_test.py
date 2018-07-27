# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
import mock
from pyramid import security
from pyramid.authorization import ACLAuthorizationPolicy

from h.models import Organization
from h.services.group_links import GroupLinksService
from h.traversal.contexts import AnnotationContext
from h.traversal.contexts import GroupContext
from h.traversal.contexts import OrganizationContext


@pytest.mark.usefixtures('group_service', 'links_service')
class TestAnnotationContext(object):
    def test_links(self, group_service, links_service):
        ann = mock.Mock()
        res = AnnotationContext(ann, group_service, links_service)

        result = res.links

        links_service.get_all.assert_called_once_with(ann)
        assert result == links_service.get_all.return_value

    def test_link(self, group_service, links_service):
        ann = mock.Mock()
        res = AnnotationContext(ann, group_service, links_service)

        result = res.link('json')

        links_service.get.assert_called_once_with(ann, 'json')
        assert result == links_service.get.return_value

    def test_acl_private(self, factories, group_service, links_service):
        ann = factories.Annotation(shared=False, userid='saoirse')
        res = AnnotationContext(ann, group_service, links_service)
        actual = res.__acl__()
        expect = [(security.Allow, 'saoirse', 'read'),
                  (security.Allow, 'saoirse', 'admin'),
                  (security.Allow, 'saoirse', 'update'),
                  (security.Allow, 'saoirse', 'delete'),
                  security.DENY_ALL]
        assert actual == expect

    def test_acl_shared_admin_perms(self, factories, group_service, links_service):
        """
        Shared annotation contexts should still only give admin/update/delete
        permissions to the owner.
        """
        policy = ACLAuthorizationPolicy()

        ann = factories.Annotation(shared=False, userid='saoirse')
        res = AnnotationContext(ann, group_service, links_service)

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
        res = AnnotationContext(ann, group_service, links_service)

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
        Shared annotation contexts should delegate their 'read' permission to
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
        res = AnnotationContext(ann, group_service, links_service)

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


@pytest.mark.usefixtures('links_svc')
class TestGroupContext(object):

    def test_it_returns_group_model_as_property(self, factories, pyramid_request):
        group = factories.Group()

        group_context = GroupContext(group, pyramid_request)

        assert group_context.group == group

    def test_it_proxies_links_to_svc(self, factories, links_svc, pyramid_request):
        group = factories.Group()

        group_context = GroupContext(group, pyramid_request)

        assert group_context.links == links_svc.get_all.return_value

    def test_it_returns_pubid_as_id(self, factories, pyramid_request):
        group = factories.Group()

        group_context = GroupContext(group, pyramid_request)

        assert group_context.id == group.pubid  # NOT the group.id

    def test_it_expands_organization(self, factories, pyramid_request):
        group = factories.Group()

        group_context = GroupContext(group, pyramid_request)

        assert isinstance(group_context.organization, OrganizationContext)


@pytest.mark.usefixtures('organization_routes')
class TestOrganizationContext(object):

    def test_it_returns_organization_model_as_property(self, factories, pyramid_request):
        organization = factories.Organization()

        organization_context = OrganizationContext(organization, pyramid_request)

        assert organization_context.organization == organization

    def test_it_returns_pubid_as_id(self, factories, pyramid_request):
        organization = factories.Organization()

        organization_context = OrganizationContext(organization, pyramid_request)

        assert organization_context.id != organization.id
        assert organization_context.id == organization.pubid

    def test_it_returns_links_property(self, factories, pyramid_request):
        organization = factories.Organization()

        organization_context = OrganizationContext(organization, pyramid_request)

        assert organization_context.links == {}

    def test_it_returns_logo_property_as_route_url(self, factories, pyramid_request):
        fake_logo = '<svg>H</svg>'
        pyramid_request.route_url = mock.Mock()

        organization = factories.Organization(logo=fake_logo)

        organization_context = OrganizationContext(organization, pyramid_request)
        logo = organization_context.logo

        pyramid_request.route_url.assert_called_with('organization_logo', pubid=organization.pubid)
        assert logo is not None

    def test_it_returns_none_for_logo_if_no_logo(self, factories, pyramid_request):
        pyramid_request.route_url = mock.Mock()

        organization = factories.Organization(logo=None)

        organization_context = OrganizationContext(organization, pyramid_request)
        logo = organization_context.logo

        pyramid_request.route_url.assert_not_called
        assert logo is None

    def test_default_property_if_not_default_organization(self, factories, pyramid_request):
        organization = factories.Organization()

        organization_context = OrganizationContext(organization, pyramid_request)

        assert organization_context.default is False

    def test_default_property_if_default_organization(self, factories, pyramid_request):
        organization = Organization.default(pyramid_request.db)

        organization_context = OrganizationContext(organization, pyramid_request)

        assert organization_context.default is True


class FakeGroup(object):
    def __init__(self, principals):
        self.__acl__ = [(security.Allow, p, 'read') for p in principals]


@pytest.fixture
def links_svc(pyramid_config):
    svc = mock.create_autospec(GroupLinksService, spec_set=True, instance=True)
    pyramid_config.register_service(svc, name='group_links')
    return svc


@pytest.fixture
def organization_routes(pyramid_config):
    pyramid_config.add_route('organization_logo', '/organization/{pubid}/logo')
