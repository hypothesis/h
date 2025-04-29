from pyramid.httpexceptions import HTTPNoContent

from h import events
from h.schemas.api.moderation import ChangeAnnotationModerationStatusSchema
from h.schemas.util import validate_query_params
from h.security import Permission
from h.services import AnnotationWriteService
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
    request.find_service(AnnotationWriteService).hide(context.annotation, request.user)

    event = events.AnnotationEvent(request, context.annotation.id, "update")
    request.notify_after_commit(event)

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
    request.find_service(AnnotationWriteService).unhide(
        context.annotation, request.user
    )

    event = events.AnnotationEvent(request, context.annotation.id, "update")
    request.notify_after_commit(event)

    return HTTPNoContent()


@api_config(
    versions=["v1", "v2"],
    route_name="api.annotation_moderation",
    request_method="PATCH",
    link_name="annotation_moderation",
    permission=Permission.Annotation.MODERATE,
)
def change_annotation_moderation_status(context, request):
    params = validate_query_params(
        ChangeAnnotationModerationStatusSchema(), request.params
    )
    status = params["moderation_status"]
    request.find_service(name="annotation_moderation").set_status(
        context.annotation, request.user, status
    )
    event = events.AnnotationEvent(request, context.annotation.id, "update")
    request.notify_after_commit(event)

    return request.find_service(name="annotation_json").present_for_user(
        annotation=context.annotation, user=request.user
    )
