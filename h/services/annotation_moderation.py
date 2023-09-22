from h.events import AnnotationEvent
from h.models import AnnotationModeration


class AnnotationModerationService:
    def __init__(self, db, request):
        self._db = db
        self._request = request

    def all_hidden(self, annotation_ids):
        """
        Check which of the given annotation ids is hidden.

        :param annotation_ids: The ids of the annotations to check.
        :returns: The subset of the annotation ids that are hidden.
        """
        if not annotation_ids:
            return set()

        query = self._db.query(AnnotationModeration.annotation_id).filter(
            AnnotationModeration.annotation_id.in_(annotation_ids)
        )

        return {m.annotation_id for m in query}

    def create(self, annotation):
        if not annotation.is_hidden:
            annotation.moderation = AnnotationModeration()

        event = AnnotationEvent(self._request, annotation.id, "update")
        self._request.notify_after_commit(event)

    def delete(self, annotation):
        annotation.moderation = None

        event = AnnotationEvent(self._request, annotation.id, "update")
        self._request.notify_after_commit(event)


def annotation_moderation_service_factory(_context, request):
    return AnnotationModerationService(request.db, request)
