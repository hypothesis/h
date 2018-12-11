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

from h.auth import role
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

        # For shared annotations, some permissions are derived from the
        # permissions for this annotation's containing group.
        # Otherwise they are derived from the annotation's creator
        if self.annotation.shared:
            for principal in self._group_principals(self.group, "read"):
                acl.append((Allow, principal, "read"))

            for principal in self._group_principals(self.group, "flag"):
                acl.append((Allow, principal, "flag"))

            for principal in self._group_principals(self.group, "moderate"):
                acl.append((Allow, principal, "moderate"))

        else:
            acl.append((Allow, self.annotation.userid, "read"))
            # Flagging one's own private annotations is nonsensical,
            # but from an authz perspective, allowed. It is up to services/views
            # to handle these situations appropriately
            acl.append((Allow, self.annotation.userid, "flag"))

        # The user who created the annotation always has the following permissions
        for action in ["admin", "update", "delete"]:
            acl.append((Allow, self.annotation.userid, action))

        # If we haven't explicitly authorized it, it's not allowed.
        acl.append(DENY_ALL)

        return acl

    @staticmethod
    def _group_principals(group, principal):
        if group is None:
            return []
        principals = principals_allowed_by_permission(group, principal)
        return principals


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
            return self.request.route_url(
                "organization_logo", pubid=self.organization.pubid
            )
        return None


class GroupContext(object):
    """Context for group-based views."""

    def __init__(self, group, request):
        self.request = request
        self.group = group
        self.links_service = self.request.find_service(name="group_links")

    @property
    def id(self):
        return self.group.pubid  # Web-facing unique ID for this resource

    @property
    def links(self):
        return self.links_service.get_all(self.group)

    @property
    def organization(self):
        if self.group.organization is not None:
            return OrganizationContext(self.group.organization, self.request)
        return None


class GroupUpsertContext(object):
    """Context for group UPSERT"""

    def __init__(self, group, request):
        self._request = request
        self.group = group

    def __acl__(self):
        """
        Get the ACL from the group model or set "upsert" for all users in absence of model

        If there is a group model, get the ACL from there. Otherwise, return an
        ACL that sets the "upsert" permission for authenticated requests that have
        a real user associated with them via :attr:`h.auth.role.User`.

        The "upsert" permission is an unusual hybrid. It has a different meaning
        depending on the upsert situation.

        If there is no group associated with the context, the "upsert" permission
        should be given to all real users such that they may use the UPSERT endpoint
        to create a new group. However, if there is a group associated with the
        context, the "upsert" permission is managed by the model. The model only
        applies "upsert" for the group's creator. This will allow the endpoint to
        support updating a specific group (model), but only if the request's
        user should be able to update the group.
        """

        # TODO: This and ``GroupContext`` can likely be merged once ``GroupContext``
        # is used more resource-appropriately and returned by :class:`h.traversal.roots.GroupRoot`
        # during traversal
        if self.group is not None:
            return self.group.__acl__()
        return [(Allow, role.User, "upsert")]
