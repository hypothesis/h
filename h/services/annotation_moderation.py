from h.events import AnnotationAction
from h.models import Annotation, ModerationLog, ModerationStatus, User


class AnnotationModerationService:
    def __init__(self, session):
        self._session = session

    def all_hidden(self, annotation_ids: str) -> set[str]:
        """
        Check which of the given annotation ids is hidden.

        :param annotation_ids: The ids of the annotations to check.
        :returns: The subset of the annotation ids that are hidden.
        """
        if not annotation_ids:
            return set()

        query = self._session.query(Annotation).filter(
            Annotation.id.in_(annotation_ids)
        )
        return {a.id for a in query if a.is_hidden}

    def set_status(
        self,
        annotation: Annotation,
        status: ModerationStatus | None,
        user: User | None = None,
    ) -> None:
        """Set the moderation status for an annotation."""
        if status and status != annotation.moderation_status:
            self._session.add(
                ModerationLog(
                    annotation=annotation,
                    old_moderation_status=annotation.moderation_status,
                    new_moderation_status=status.value,
                    moderator=user,
                )
            )
            annotation.moderation_status = status

    def update_status(self, action: AnnotationAction, annotation: Annotation) -> None:
        """Change the moderation status of an annotation based on the action taken."""
        new_status = None

        if not annotation.moderation_status and annotation.shared:
            # If an annotation is not private but doesn't have a moderation status
            # it means that the moderation status hasn't been migrated yet.
            # Set the default `APPROVED` status
            if action == "update":
                # If the annotation was updated we want to record this in the moderation log
                self.set_status(annotation, ModerationStatus.APPROVED)
            else:
                annotation.moderation_status = ModerationStatus.APPROVED

        if not annotation.shared:
            return

        pre_moderated = annotation.group.pre_moderated
        if action == "create":
            if pre_moderated:
                new_status = ModerationStatus.PENDING
            else:
                new_status = ModerationStatus.APPROVED
        elif action == "update":
            if (
                pre_moderated
                and annotation.moderation_status == ModerationStatus.APPROVED
            ):
                new_status = ModerationStatus.PENDING

            if annotation.moderation_status == ModerationStatus.DENIED:
                new_status = ModerationStatus.PENDING

        self.set_status(annotation, new_status)


def annotation_moderation_service_factory(_context, request):
    return AnnotationModerationService(request.db)
