# -*- coding: utf-8 -*-
"""
"Context resource" objects for Pyramid views.

Context objects are reusable components that represent "the context of a view"
or "the subject of a view".

They can do things like wrap a model object (or multiple model objects) and,
since they have access to the ``request``  object, provide access to properties
that you need the request to compute such as permissions, or route URLs for a
wrapped model object. The view, or any code that the view calls and passes the
context object into, can then make use of these properties.

These context objects are returned by the root resources in
:py:mod:`h.traversal.roots` if the route is configured to use one of those root
factories (see the :py:mod:`h.traversal.roots` for usage).

For such a route Pyramid will conveniently pass the found context object into
the view callable as the ``context`` argument.

"""
from __future__ import unicode_literals

from pyramid.security import DENY_ALL
from pyramid.security import Allow
from pyramid.security import principals_allowed_by_permission

from h.models.organization import ORGANIZATION_DEFAULT_PUBID


class AnnotationContext(object):
    """Context for annotation-based views."""

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


class AuthClientContext(object):
    """Context for AuthClient-based views."""

    def __init__(self, auth_client):
        self.auth_client = auth_client


class OrganizationContext(object):
    """Context for organization-based views."""

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


class GroupContext(object):
    """Context for group-based views."""

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
        return OrganizationContext(self.group.organization, self.request)
