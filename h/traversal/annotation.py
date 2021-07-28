from pyramid.security import (
    DENY_ALL,
    Allow,
    Authenticated,
    principals_allowed_by_permission,
)

from h import storage
from h.interfaces import IGroupService
from h.security.permissions import Permission
from h.traversal.group import GroupContext
from h.traversal.root import RootFactory


class AnnotationRoot(RootFactory):
    """Root factory for routes whose context is an `AnnotationContext`."""

    __acl__ = [(Allow, Authenticated, Permission.Annotation.CREATE)]

    def __getitem__(self, annotation_id):
        annotation = storage.fetch_annotation(self.request.db, annotation_id)
        if annotation is None:
            raise KeyError()

        group_service = self.request.find_service(IGroupService)
        links_service = self.request.find_service(name="links")
        return AnnotationContext(annotation, group_service, links_service)


class AnnotationContext:
    """Context for annotation-based views."""

    annotation = None

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

        acl = list(self._read_principals())

        # For shared annotations, some permissions are derived from the
        # permissions for this annotation's containing group.
        # Otherwise they are derived from the annotation's creator
        if self.annotation.shared:
            for principal in self._group_principals(self.group, Permission.Group.FLAG):
                acl.append((Allow, principal, Permission.Annotation.FLAG))

            for principal in self._group_principals(
                self.group, Permission.Group.MODERATE
            ):
                acl.append((Allow, principal, Permission.Annotation.MODERATE))

        else:
            # Flagging one's own private annotations is nonsensical,
            # but from an authz perspective, allowed. It is up to services/views
            # to handle these situations appropriately
            acl.append((Allow, self.annotation.userid, Permission.Annotation.FLAG))

        # The user who created the annotation always has the these permissions
        acl.append((Allow, self.annotation.userid, Permission.Annotation.UPDATE))
        acl.append((Allow, self.annotation.userid, Permission.Annotation.DELETE))

        # If we haven't explicitly authorized it, it's not allowed.
        acl.append(DENY_ALL)

        return acl

    def _read_principals(self):
        if self.annotation.shared:
            for principal in self._group_principals(self.group, Permission.Group.READ):
                yield Allow, principal, Permission.Annotation.READ
        else:
            yield Allow, self.annotation.userid, Permission.Annotation.READ

    @staticmethod
    def _group_principals(group, permission):
        if group is None:
            return []

        return principals_allowed_by_permission(GroupContext(group), permission)
