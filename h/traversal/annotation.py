from dataclasses import dataclass

from h import storage
from h.models import Annotation
from h.traversal.root import RootFactory


class AnnotationRoot(RootFactory):
    """Root factory for routes whose context is an `AnnotationContext`."""

    def __getitem__(self, annotation_id):
        annotation = storage.fetch_annotation(self.request.db, annotation_id)
        if annotation is None:
            raise KeyError()

        return AnnotationContext(annotation)


@dataclass
class AnnotationContext:
    """Context for annotation-based views."""

    annotation: Annotation

    @property
    def group(self):
        return self.annotation.group
