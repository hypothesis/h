import colander
from pyramid import httpexceptions

from h.models.annotation import ModerationStatus


class ModerationStatusNode(colander.SchemaNode):
    schema_type = colander.String
    validator = colander.OneOf(["APPROVED", "PENDING", "DENIED", "SPAM"])

    def deserialize(self, cstruct):
        return ModerationStatus(cstruct) if cstruct else None


class ChangeAnnotationModerationStatusSchema(colander.Schema):
    """Schema for validating change-annotation-moderation-status API data."""

    moderation_status = ModerationStatusNode()
    annotation_updated = colander.SchemaNode(
        colander.DateTime(),
        description="Sentinel value to avoid conflicting updates. It should be match the current value of annotation.updated",
    )

    def __init__(self, annotation):
        super().__init__()

        self._annotation = annotation

    def validator(self, _node, cstruct):
        if (
            self._annotation.updated.timestamp()
            != cstruct["annotation_updated"].timestamp()
        ):
            raise httpexceptions.HTTPConflict(
                explanation="The annotation has been updated since the moderation status was set."
            )
