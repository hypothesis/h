from typing import Literal

AnnotationAction = Literal["create", "update", "delete"]


class AnnotationEvent:
    """An event representing an action on an annotation."""

    def __init__(self, request, annotation_id, action: AnnotationAction):
        self.request = request
        self.annotation_id = annotation_id
        self.action = action
