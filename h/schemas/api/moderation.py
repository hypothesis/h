from datetime import UTC

import colander
from pyramid import httpexceptions

from h.models import Annotation


class ModerationStatusNode(colander.SchemaNode):
    schema_type = colander.String
    validator = colander.OneOf(["APPROVED", "PENDING", "DENIED", "SPAM"])


class ChangeAnnotationModerationStatusSchema(colander.Schema):
    """Schema for validating change-annotation-moderation-status API data."""

    moderation_status = ModerationStatusNode(
        missing=colander.required, description="New moderation status to be set"
    )
    current_moderation_status = ModerationStatusNode(
        missing=None,
        description="Sentinel value to avoid conflicting updates. If provided, it should match the current value of annotation.moderation_status",
    )
    annotation_updated = colander.SchemaNode(
        colander.DateTime(),
        description="Sentinel value to avoid conflicting updates. It should match the current value of annotation.updated",
    )

    def __init__(self, annotation: Annotation):
        super().__init__()

        self._annotation = annotation

    def validator(self, _node, cstruct):
        if (
            cstruct["current_moderation_status"]
            and cstruct["current_moderation_status"]
            != self._annotation.moderation_status.value
        ):
            raise httpexceptions.HTTPConflict(
                detail="The annotation has been moderated since it was loaded."
            )

        # Annotations are updated in the DB without timezone but they are implicitly UTC
        annotation_updated = self._annotation.updated.replace(tzinfo=UTC).timestamp()
        if annotation_updated != cstruct["annotation_updated"].timestamp():
            raise httpexceptions.HTTPConflict(
                detail="The annotation has been updated since the moderation status was set."
            )
