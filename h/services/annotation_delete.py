from datetime import datetime, timedelta

from h.events import AnnotationEvent
from h.models import Annotation
from h.services.annotation_write import AnnotationWriteService


class AnnotationDeleteService:
    def __init__(self, request, annotation_write):
        self.request = request
        self.annotation_write = annotation_write

    def delete(self, annotation):
        """
        Delete the given annotation.

        :param annotation: the annotation to be deleted
        :type annotation: h.models.Annotation
        """
        annotation.updated = datetime.utcnow()
        annotation.deleted = True

        self.annotation_write.upsert_annotation_slim(annotation)

        event = AnnotationEvent(self.request, annotation.id, "delete")
        self.request.notify_after_commit(event)

    def delete_annotations(self, annotations):
        """
        Delete the given iterable of annotations.

        :param annotations: the iterable of annotations to be deleted
        :type annotations: iterable of h.models.Annotation
        """
        for ann in annotations:
            self.delete(ann)

    def bulk_delete(self):
        """Expunge annotations marked as deleted from the database."""
        self.request.db.query(Annotation).filter_by(deleted=True).filter(
            # Deletes all annotations flagged as deleted more than 10 minutes ago. This
            # buffer period should ensure that this task doesn't delete annotations
            # deleted just before the task runs, which haven't yet been processed by the
            # streamer.
            Annotation.updated
            < datetime.utcnow() - timedelta(minutes=10)
        ).delete()


def annotation_delete_service_factory(_context, request):
    return AnnotationDeleteService(
        request, request.find_service(AnnotationWriteService)
    )
