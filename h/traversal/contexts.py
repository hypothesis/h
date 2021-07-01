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
from pyramid.security import DENY_ALL, Allow, principals_allowed_by_permission


class AnnotationContext:
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

    def _read_principals(self):
        if self.annotation.shared:
            for principal in self._group_principals(self.group, "read"):
                yield Allow, principal, "read"
        else:
            yield Allow, self.annotation.userid, "read"

    def __acl__(self):
        """Return a Pyramid ACL for this annotation."""
        # If the annotation has been deleted, nobody has any privileges on it
        # any more.
        if self.annotation.deleted:
            return [DENY_ALL]

        acl = list(self._read_principals())

        # For shared annotations, some permissions are derived from the
        # permissions for this annotation's containing group.
        # Otherwise they are derived from the annotation's creator
        if self.annotation.shared:
            for principal in self._group_principals(self.group, "flag"):
                acl.append((Allow, principal, "flag"))

            for principal in self._group_principals(self.group, "moderate"):
                acl.append((Allow, principal, "moderate"))

        else:
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


class UserContext:
    """
    Context for user-centered views

    .. todo:: Most views still traverse using ``username`` and work directly
       with User models (:class:`h.models.User`). This context should be
       expanded as we continue to move over to a more resource-based approach.
    """

    def __init__(self, user):
        self.user = user

    def __acl__(self):
        """
        Set the "read" permission for AuthClients that have a matching authority
        to the user. This supercedes the ACL in :class:`h.models.User`.

        .. todo:: This ACL should be expanded (as needed) as more views make use of
        a context versus a model directly.
        """
        acl = []

        user_authority_principal = f"client_authority:{self.user.authority}"
        acl.append((Allow, user_authority_principal, "read"))

        return acl
