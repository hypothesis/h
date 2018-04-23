# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid.security import (
    ALL_PERMISSIONS,
    DENY_ALL,
    Allow,
    principals_allowed_by_permission,
)
from sqlalchemy.orm import exc

from h import storage
from h.models import AuthClient
from h.models import Group
from h.models import Organization
from h.models.organization import ORGANIZATION_DEFAULT_PUBID
from h.auth import role
from h.interfaces import IGroupService


class Root(object):
    __acl__ = [
        (Allow, role.Staff, 'admin_index'),
        (Allow, role.Staff, 'admin_groups'),
        (Allow, role.Staff, 'admin_mailer'),
        (Allow, role.Staff, 'admin_organizations'),
        (Allow, role.Staff, 'admin_users'),
        (Allow, role.Admin, ALL_PERMISSIONS),
        DENY_ALL
    ]

    def __init__(self, request):
        self.request = request


class AnnotationResourceFactory(object):
    def __init__(self, request):
        self.request = request

    def __getitem__(self, id):
        annotation = storage.fetch_annotation(self.request.db, id)
        if annotation is None:
            raise KeyError()

        group_service = self.request.find_service(IGroupService)
        links_service = self.request.find_service(name='links')
        return AnnotationResource(annotation, group_service, links_service)


class AnnotationResource(object):
    def __init__(self, annotation, group_service, links_service):
        self.group_service = group_service
        self.links_service = links_service
        self.annotation = annotation

    @property
    def group(self):
        return self.group_service.find(self.annotation.groupid)

    @property
    def links(self):
        return self.links_service.get_all(self.annotation)

    def link(self, name):
        return self.links_service.get(self.annotation, name)

    def __acl__(self):
        """Return a Pyramid ACL for this annotation."""
        # If the annotation has been deleted, nobody has any privileges on it
        # any more.
        if self.annotation.deleted:
            return [DENY_ALL]

        acl = []
        if self.annotation.shared:
            for principal in self._group_principals(self.group):
                acl.append((Allow, principal, 'read'))
        else:
            acl.append((Allow, self.annotation.userid, 'read'))

        for action in ['admin', 'update', 'delete']:
            acl.append((Allow, self.annotation.userid, action))

        # If we haven't explicitly authorized it, it's not allowed.
        acl.append(DENY_ALL)

        return acl

    @staticmethod
    def _group_principals(group):
        if group is None:
            return []
        return principals_allowed_by_permission(group, 'read')


class AuthClientFactory(object):

    def __init__(self, request):
        self.request = request

    def __getitem__(self, client_id):
        try:
            client = self.request.db.query(AuthClient) \
                                    .filter_by(id=client_id).one()

            # Inherit global ACL.
            # See `pyramid.authorization.ACLAuthorizationPolicy` docs.
            #
            # Other resources do not currently do this, but we rely on it for
            # this resource because it is used within the /admin pages.
            client.__parent__ = Root(self.request)

            return client
        except:  # noqa: E722
            # No such client found or not a valid UUID.
            raise KeyError()


class OrganizationFactory(object):
    def __init__(self, request):
        self.request = request

    def __getitem__(self, pubid):
        try:
            org = self.request.db.query(Organization).filter_by(pubid=pubid).one()

            # Inherit global ACL. See comments in `AuthClientFactory`.
            org.__parent__ = Root(self.request)

            return org
        except exc.NoResultFound:
            raise KeyError()


class OrganizationResource(object):
    def __init__(self, organization, request):
        # TODO Links service
        self.organization = organization
        self.request = request

    @property
    def id(self):
        return self.organization.pubid  # Web-facing unique ID for this resource

    @property
    def default(self):
        return self.id == ORGANIZATION_DEFAULT_PUBID

    @property
    def links(self):
        # TODO
        return {}

    @property
    def logo(self):
        if self.organization.logo:
            return self.request.route_url('organization_logo',
                                          pubid=self.organization.pubid)
        return None


class OrganizationLogoFactory(object):
    def __init__(self, request):
        self.request = request
        self.organization_factory = OrganizationFactory(self.request)

    def __getitem__(self, pubid):
        # This will raise KeyError if the organization doesn't exist.
        organization = self.organization_factory[pubid]

        if not organization.logo:
            raise KeyError()

        return organization.logo


class GroupFactory(object):
    def __init__(self, request):
        self.request = request

    def __getitem__(self, pubid):
        try:
            return self.request.db.query(Group).filter_by(pubid=pubid).one()
        except exc.NoResultFound:
            raise KeyError()


class GroupResource(object):
    def __init__(self, group, request):
        self.request = request
        self.group = group
        self.links_service = self.request.find_service(name='group_links')

    @property
    def id(self):
        return self.group.pubid  # Web-facing unique ID for this resource

    @property
    def links(self):
        return self.links_service.get_all(self.group)

    @property
    def organization(self):
        return OrganizationResource(self.group.organization, self.request)


class UserFactory(object):
    """Root resource for routes that look up User objects by traversal."""

    def __init__(self, request):
        self.request = request
        self.user_svc = self.request.find_service(name='user')

    def __getitem__(self, username):
        user = self.user_svc.fetch(username, self.request.authority)

        if not user:
            raise KeyError()

        return user
