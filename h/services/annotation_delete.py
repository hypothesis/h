from datetime import datetime, timedelta

from pyramid.request import Request
from sqlalchemy import delete, select

from h.events import AnnotationEvent
from h.models import Annotation
from h.services.annotation_write import AnnotationWriteService
from h.services.job_queue import JobQueueService


class AnnotationDeleteService:
    def __init__(
        self,
        request: Request,
        annotation_write: AnnotationWriteService,
        job_queue: JobQueueService,
    ):
        self.request = request
        self.annotation_write = annotation_write
        self.job_queue = job_queue

    def delete(self, annotation):
        """
        Delete the given annotation.

        :param annotation: the annotation to be deleted
        :type annotation: h.models.Annotation
        """
        annotation.updated = datetime.utcnow()
        annotation.deleted = True
        self.job_queue.add_by_id(
            name="sync_annotation",
            annotation_id=annotation.id,
            tag="AnnotationDeleteService.delete_annotation",
            schedule_in=60,
        )

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
        self.request.db.execute(
            delete(Annotation).where(
                Annotation.id.in_(
                    select(
                        select(Annotation.id)
                        .where(Annotation.deleted.is_(True))
                        # Wait ten minutes before expunging an annotation to
                        # give the streamer time to process the deletion.
                        .where(
                            Annotation.updated
                            < datetime.utcnow() - timedelta(minutes=10)
                        )
                        # Only expunge up to 1000 annotations at a time to
                        # avoid long-running DB queries. This method is called
                        # periodically so eventually all deleted annotations
                        # will get expunged.
                        .limit(1000)
                        .cte()
                    )
                )
            )
        )


def annotation_delete_service_factory(_context, request):
    return AnnotationDeleteService(
        request,
        request.find_service(AnnotationWriteService),
        request.find_service(name="queue_service"),
    )
