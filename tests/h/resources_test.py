# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
from mock import Mock

from pyramid import security
from pyramid.authorization import ACLAuthorizationPolicy

from h.resources import AnnotationResource, AnnotationResourceFactory


@pytest.mark.usefixtures('group_service', 'links_service')
class TestAnnotationResourceFactory(object):
    def test_get_item_fetches_annotation(self, pyramid_request, storage):
        factory = AnnotationResourceFactory(pyramid_request)

        factory['123']
        storage.fetch_annotation.assert_called_once_with(pyramid_request.db, '123')

    def test_get_item_returns_annotation_resource(self, pyramid_request, storage):
        factory = AnnotationResourceFactory(pyramid_request)
        storage.fetch_annotation.return_value = Mock()

        resource = factory['123']
        assert isinstance(resource, AnnotationResource)

    def test_get_item_resource_has_right_annotation(self, pyramid_request, storage):
        factory = AnnotationResourceFactory(pyramid_request)
        storage.fetch_annotation.return_value = Mock()

        resource = factory['123']
        assert resource.annotation == storage.fetch_annotation.return_value

    def test_get_item_raises_when_annotation_is_not_found(self, storage, pyramid_request):
        factory = AnnotationResourceFactory(pyramid_request)
        storage.fetch_annotation.return_value = None

        with pytest.raises(KeyError):
            factory['123']

    def test_get_item_has_right_group_service(self, pyramid_request, storage, group_service):
        factory = AnnotationResourceFactory(pyramid_request)
        storage.fetch_annotation.return_value = Mock()

        resource = factory['123']
        assert resource.group_service == group_service

    def test_get_item_has_right_links_service(self, pyramid_request, storage, links_service):
        factory = AnnotationResourceFactory(pyramid_request)
        storage.fetch_annotation.return_value = Mock()

        resource = factory['123']
        assert resource.links_service == links_service

    @pytest.fixture
    def storage(self, patch):
        return patch('h.resources.storage')

    @pytest.fixture
    def group_service(self, pyramid_config):
        group_service = Mock(spec_set=['find'])
        pyramid_config.register_service(group_service, iface='h.interfaces.IGroupService')
        return group_service

    @pytest.fixture
    def links_service(self, pyramid_config):
        service = Mock()
        pyramid_config.register_service(service, name='links')
        return service


@pytest.mark.usefixtures('group_service', 'links_service')
class TestAnnotationResource(object):
    def test_links(self, group_service, links_service):
        ann = Mock()
        res = AnnotationResource(ann, group_service, links_service)

        result = res.links

        links_service.get_all.assert_called_once_with(ann)
        assert result == links_service.get_all.return_value

    def test_link(self, group_service, links_service):
        ann = Mock()
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
        group_service = Mock(spec_set=['find'])
        group_service.find.side_effect = lambda groupid: groups.get(groupid)
        pyramid_config.register_service(group_service, iface='h.interfaces.IGroupService')
        return group_service

    @pytest.fixture
    def links_service(self, pyramid_config):
        service = Mock(spec_set=['get', 'get_all'])
        pyramid_config.register_service(service, name='links')
        return service


class FakeGroup(object):
    def __init__(self, principals):
        self.__acl__ = [(security.Allow, p, 'read') for p in principals]
