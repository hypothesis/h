from h.models import Annotation, AnnotationModeration, User
from h.models.annotation import ModerationStatus
from h.models.moderation_log import ModerationLog


class AnnotationModerationService:
    def __init__(self, session):
        self._session = session

    def all_hidden(self, annotation_ids):
        """
        Check which of the given annotation ids is hidden.

        :param annotation_ids: The ids of the annotations to check.
        :returns: The subset of the annotation ids that are hidden.
        """
        if not annotation_ids:
            return set()

        query = self._session.query(AnnotationModeration.annotation_id).filter(
            AnnotationModeration.annotation_id.in_(annotation_ids)
        )
        return {m.annotation_id for m in query}

    def set_status(
        self, annotation: Annotation, user: User, status: ModerationStatus | None
    ) -> None:
        """Set the moderation status for an annotation."""
        if status and status != annotation.moderation_status:
            self._session.add(
                ModerationLog(
                    annotation_id=annotation.id,
                    old_moderation_status=annotation.moderation_status,
                    new_moderation_status=status.value,
                    moderator_id=user.id,
                )
            )
            annotation.moderation_status = status

    def update_status(self, annotation: Annotation) -> None:
        if not annotation.moderation_status and annotation.shared:
            # If an annotation is not private but doesn't have a moderation status
            # it means that the moderation status hasn't been migrated yet.
            # Set the default `APPROVED` status
            annotation.moderation_status = ModerationStatus.APPROVED


def annotation_moderation_service_factory(_context, request):
    return AnnotationModerationService(request.db)
