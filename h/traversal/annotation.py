from pyramid.security import (
    DENY_ALL,
    Allow,
    Authenticated,
    principals_allowed_by_permission,
)

from h import storage
from h.interfaces import IGroupService
from h.traversal.root import RootFactory


class AnnotationRoot(RootFactory):
    """Root factory for routes whose context is an `AnnotationContext`."""

    __acl__ = [(Allow, Authenticated, "create")]

    def __getitem__(self, id_):
        annotation = storage.fetch_annotation(self.request.db, id_)
        if annotation is None:
            raise KeyError()

        group_service = self.request.find_service(IGroupService)
        links_service = self.request.find_service(name="links")
        return AnnotationContext(annotation, group_service, links_service)


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
