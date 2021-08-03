from dataclasses import dataclass

from h import storage
from h.models import Annotation
from h.security.acl import ACL
from h.traversal.root import RootFactory


class AnnotationRoot(RootFactory):
    """Root factory for routes whose context is an `AnnotationContext`."""

    def __getitem__(self, annotation_id):
        annotation = storage.fetch_annotation(self.request.db, annotation_id)
        if annotation is None:
            raise KeyError()

        return AnnotationContext(annotation)

    @classmethod
    def __acl__(cls):
        return ACL.for_annotation(annotation=None)


@dataclass
class AnnotationContext:
    """Context for annotation-based views."""

    annotation: Annotation

    def __acl__(self):
        return ACL.for_annotation(self.annotation)
