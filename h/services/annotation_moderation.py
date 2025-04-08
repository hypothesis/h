from h.events import AnnotationAction
from h.models import Annotation, AnnotationModeration, Group, User
from h.models.annotation import ModerationStatus
from h.models.annotation_moderation import ModerationLog


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

    def set_status(
        self, annotation: Annotation, user: User, status: ModerationStatus | None
    ) -> None:
        if status and status != annotation.moderation_status:
            self._session.add(
                ModerationLog(
                    annotation_id=annotation.id,
                    old_moderation_status=annotation.moderation_status,
                    new_moderation_status=status.value,
                    user_id=user.id,
                )
            )
            annotation.moderation_status = status

    def initialize_status(self, annotation):
        if not annotation.moderation_status and annotation.shared:
            # First set the right moderation status if this row as not been migrated
            # We have already migrated all moderated (hide/unhide) annotations
            # The reminding ones are either private or approved
            annotation.moderation_status = ModerationStatus.APPROVED

    def update_status(
        self, action: AnnotationAction, annotation: Annotation, group: Group
    ) -> None:
        self.initialize_status(annotation)

        if not annotation.shared:
            return

        new_status = None
        if action == "created":
            if group.pre_moderated:
                new_status = ModerationStatus.PENDING
            else:
                new_status = ModerationStatus.APPROVED
        elif (
            action == "updated"
            and group.pre_moderated
            and annotation.moderation_status != ModerationStatus.SPAM
        ):
            new_status = ModerationStatus.PENDING

        self.set_status(annotation, new_status)


def annotation_moderation_service_factory(_context, request):
    return AnnotationModerationService(request.db)
