# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid.security import (
    ALL_PERMISSIONS,
    DENY_ALL,
    Allow,
    principals_allowed_by_permission,
)

from h import storage
from h.models import AuthClient
from h.auth import role
from h.interfaces import IGroupService


class Root(object):
    __acl__ = [
        (Allow, role.Staff, 'admin_index'),
        (Allow, role.Staff, 'admin_groups'),
        (Allow, role.Staff, 'admin_mailer'),
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
            for principal in _group_principals(self.group):
                acl.append((Allow, principal, 'read'))
        else:
            acl.append((Allow, self.annotation.userid, 'read'))

        for action in ['admin', 'update', 'delete']:
            acl.append((Allow, self.annotation.userid, action))

        # If we haven't explicitly authorized it, it's not allowed.
        acl.append(DENY_ALL)

        return acl


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


def _group_principals(group):
    if group is None:
        return []
    return principals_allowed_by_permission(group, 'read')
