from pyramid.security import (
    DENY_ALL,
    Allow,
    Authenticated,
    principals_allowed_by_permission,
)

from h import storage
from h.interfaces import IGroupService
from h.security.acl import ACL
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
        return list(self.acl_for_annotation(self.annotation, self.group))

    @classmethod
    def acl_for_annotation(cls, annotation, group, allow_read_on_delete=False):
        """Return a Pyramid ACL for this annotation."""
        # If the annotation has been deleted, nobody has any privileges on it
        # any more.
        if annotation.deleted and not allow_read_on_delete:
            yield DENY_ALL
            return

        if annotation.shared:
            yield from cls._map_acls(
                ACL.for_group(group),
                {Permission.Group.READ: Permission.Annotation.READ},
            )

        else:
            yield Allow, annotation.userid, Permission.Annotation.READ

        if annotation.deleted:
            yield DENY_ALL
            return

        # For shared annotations, some permissions are derived from the
        # permissions for this annotation's containing group.
        # Otherwise they are derived from the annotation's creator
        if annotation.shared:
            yield from cls._map_acls(
                ACL.for_group(group),
                {
                    Permission.Group.FLAG: Permission.Annotation.FLAG,
                    Permission.Group.MODERATE: Permission.Annotation.MODERATE,
                },
            )

        else:
            # Flagging one's own private annotations is nonsensical,
            # but from an authz perspective, allowed. It is up to services/views
            # to handle these situations appropriately
            yield Allow, annotation.userid, Permission.Annotation.FLAG

        # The user who created the annotation always has the these permissions
        yield Allow, annotation.userid, Permission.Annotation.UPDATE
        yield Allow, annotation.userid, Permission.Annotation.DELETE

        # If we haven't explicitly authorized it, it's not allowed.
        yield DENY_ALL

    @classmethod
    def _map_acls(cls, acls, permission_map):
        for action, principal, permission in acls:
            try:
                mapped_permission = permission_map.get(permission)
            except TypeError:
                # Things like Pyramids "ALL_PERMISSIONS" can't be hashed or
                # mapped
                continue

            if mapped_permission:
                yield action, principal, mapped_permission
