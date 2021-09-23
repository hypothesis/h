from dataclasses import dataclass

from h import storage
from h.models import Annotation


@dataclass
class AnnotationContext:
    """Context for annotation-based views."""

    annotation: Annotation

    @property
    def group(self):
        return self.annotation.group


class AnnotationRoot:
    """Root factory for routes whose context is an `AnnotationContext`."""

    def __init__(self, request):
        self.request = request

    def __getitem__(self, annotation_id):
        annotation = storage.fetch_annotation(self.request.db, annotation_id)
        if annotation is None:
            raise KeyError()

        return AnnotationContext(annotation)
