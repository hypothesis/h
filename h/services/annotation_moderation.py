from h.events import AnnotationAction
from h.models import Annotation, AnnotationModeration, Group


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

        # TODO, move to the new column after migration and backfill migration
        query = self._session.query(AnnotationModeration.annotation_id).filter(
            AnnotationModeration.annotation_id.in_(annotation_ids)
        )
        return {m.annotation_id for m in query}

    def set_status(self, annotation, status):
        # If we get an explict status, we set it
        annotation.moderation_status = status

    def update_status(
        self, action: AnnotationAction, annotation: Annotation, group: Group
    ) -> None:
        if not annotation.moderation_status:
            # First set the right moderation status if this row as not been migrated
            # We have already migrated all moderated (hide/unhide) annotations
            # The reminding ones are either private
            if annotation.private:
                annotation.moderation_status = Annotation.ModerationStatus.PRIVATE
            else:
                annotation.moderation_status = Annotation.ModerationStatus.APPROVED

        if action == "created":
            if annotation.private:
                annotation.moderation_status = Annotation.ModerationStatus.PRIVATE
            elif group.pre_moderated:
                annotation.moderation_status = Annotation.ModerationStatus.PENDING
            else:
                annotation.moderation_status = Annotation.ModerationStatus.APPROVED
        elif action == "updated" and group.pre_moderated:
            annotation.moderation_status = Annotation.ModerationStatus.PENDING


def annotation_moderation_service_factory(_context, request):
    return AnnotationModerationService(request.db)
