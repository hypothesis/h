from h import storage
from h.security.acl import ACL
from h.traversal.root import RootFactory


class AnnotationRoot(RootFactory):
    """Root factory for routes whose context is an `AnnotationContext`."""

    def __getitem__(self, annotation_id):
        annotation = storage.fetch_annotation(self.request.db, annotation_id)
        if annotation is None:
            raise KeyError()

        links_service = self.request.find_service(name="links")
        return AnnotationContext(annotation, links_service)

    @classmethod
    def __acl__(cls):
        return ACL.for_annotation(annotation=None)


class AnnotationContext:
    """Context for annotation-based views."""

    annotation = None

    def __init__(self, annotation, links_service, allow_read_on_delete=False):
        self.links_service = links_service
        self.annotation = annotation
        self.allow_read_on_delete = allow_read_on_delete

    @property
    def group(self):
        return self.annotation.group

    @property
    def links(self):
        return self.links_service.get_all(self.annotation)

    def link(self, name):
        return self.links_service.get(self.annotation, name)

    def __acl__(self):
        return ACL.for_annotation(self.annotation, self.allow_read_on_delete)
