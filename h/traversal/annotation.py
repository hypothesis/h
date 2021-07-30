from pyramid.security import Allow, Authenticated

from h import storage
from h.interfaces import IGroupService
from h.security.acl import ACL
from h.security.permissions import Permission
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

    def __init__(
        self, annotation, group_service, links_service, allow_read_on_delete=False
    ):
        self.group_service = group_service
        self.links_service = links_service
        self.annotation = annotation
        self.allow_read_on_delete = allow_read_on_delete

    @property
    def group(self):
        return self.group_service.find(self.annotation.groupid)

    @property
    def links(self):
        return self.links_service.get_all(self.annotation)

    def link(self, name):
        return self.links_service.get(self.annotation, name)

    def __acl__(self):
        return ACL.for_annotation(
            self.annotation, self.group, self.allow_read_on_delete
        )
