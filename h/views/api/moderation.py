from pyramid.httpexceptions import HTTPNoContent

from h import events
from h.models.annotation import ModerationStatus
from h.schemas.api.moderation import ChangeAnnotationModerationStatusSchema
from h.schemas.util import validate_json
from h.security import Permission
from h.services import AnnotationWriteService
from h.tasks.moderation import send_moderation_email
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
    moderation_log = request.find_service(name="annotation_moderation").set_status(
        context.annotation, ModerationStatus.DENIED, request.user
    )
    print("moderation_log", moderation_log)
    if moderation_log:
        _notify_moderation_change(request, moderation_log)

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
    moderation_log = request.find_service(name="annotation_moderation").set_status(
        context.annotation, ModerationStatus.APPROVED, request.user
    )
    print("moderation_log", moderation_log)
    if moderation_log:
        _notify_moderation_change(request, moderation_log)

    return HTTPNoContent()


@api_config(
    versions=["v1", "v2"],
    route_name="api.annotation_moderation",
    request_method="PATCH",
    link_name="annotation_moderation",
)
def change_annotation_moderation_status(context, request):
    params = validate_json(
        ChangeAnnotationModerationStatusSchema(context.annotation), request
    )
    status = params["moderation_status"]
    moderation_log = request.find_service(name="annotation_moderation").set_status(
        context.annotation, request.user, status
    )
    if moderation_log:
        _notify_moderation_change(request, moderation_log)

    return request.find_service(name="annotation_json").present_for_user(
        annotation=context.annotation, user=request.user
    )


def _notify_moderation_change(request, moderation_log):
    annotation_id = moderation_log.annotation.id

    event = events.AnnotationEvent(request, annotation_id, "update")
    request.notify_after_commit(event)
    request.db.flush()
    send_moderation_email.apply_async(
        kwargs={
            "annotation_id": moderation_log.annotation_id,
            "moderation_datetime_iso": moderation_log.created.isoformat(),
        },
        # countdown=60 * 3,
    )
