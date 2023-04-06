from dataclasses import dataclass

from h.models import Annotation
from h.services import AnnotationService


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
        annotation = self.request.find_service(AnnotationService).get_annotation_by_id(
            annotation_id
        )
        if annotation is None:
            raise KeyError()

        return AnnotationContext(annotation)
