from pyramid.httpexceptions import HTTPNoContent

from h import events
from h.models.annotation import ModerationStatus
from h.schemas.api.moderation import ChangeAnnotationModerationStatusSchema
from h.schemas.util import validate_json
from h.security import Permission
from h.views.api.config import api_config


@api_config(
    versions=["v1", "v2"],
    route_name="api.annotation_hide",
    request_method="PUT",
    link_name="annotation.hide",
    description="Hide an annotation as a group moderator",
    permission=Permission.Annotation.MODERATE,
)
def hide(context, request):
    request.find_service(name="annotation_moderation").set_status(
        context.annotation, ModerationStatus.SPAM, request.user
    )
    _notify_moderation_change(request, context.annotation.id)

    return HTTPNoContent()


@api_config(
    versions=["v1", "v2"],
    route_name="api.annotation_hide",
    request_method="DELETE",
    link_name="annotation.unhide",
    description="Unhide an annotation as a group moderator",
    permission=Permission.Annotation.MODERATE,
)
def unhide(context, request):
    request.find_service(name="annotation_moderation").set_status(
        context.annotation, ModerationStatus.APPROVED, request.user
    )
    _notify_moderation_change(request, context.annotation.id)

    return HTTPNoContent()


@api_config(
    versions=["v1", "v2"],
    route_name="api.annotation_moderation",
    request_method="PATCH",
    link_name="annotation.moderate",
    permission=Permission.Annotation.MODERATE,
)
def change_annotation_moderation_status(context, request):
    params = validate_json(
        ChangeAnnotationModerationStatusSchema(context.annotation), request
    )
    status = ModerationStatus(params["moderation_status"])
    moderation_log = request.find_service(name="annotation_moderation").set_status(
        context.annotation, status, request.user
    )

    _notify_moderation_change(request, context.annotation.id, moderation_log)

    return request.find_service(name="annotation_json").present_for_user(
        annotation=context.annotation, user=request.user
    )


def _notify_moderation_change(request, annotation_id, moderation_log=None):
    event = events.AnnotationEvent(request, annotation_id, "update")
    request.notify_after_commit(event)

    if moderation_log:
        moderation_event = events.ModeratedAnnotationEvent(
            request, moderation_log_id=moderation_log.id
        )
        request.notify_after_commit(moderation_event)
