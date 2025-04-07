from pyramid.httpexceptions import HTTPNoContent

from h import events
from h.models import Annotation
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
def create(context, request):
    request.find_service(AnnotationWriteService).hide(context.annotation)

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
def delete(context, request):
    request.find_service(AnnotationWriteService).unhide(context.annotation)

    event = events.AnnotationEvent(request, context.annotation.id, "update")
    request.notify_after_commit(event)

    return HTTPNoContent()


@api_config(
    versions=["v1", "v2"],
    route_name="api.annotation_moderation",
    request_method="PATCH",
    link_name="annotation_moderation",
    # permission=Permission.Annotation.MODERATE,
)
def change_annotation_moderation_status(context, request):
    status = Annotation.ModerationStatus(request.json_body["moderation_status"].upper())
    request.find_service(name="annotation_moderation").set_status(
        context.annotation, status
    )

    annotation_json_service = request.find_service(name="annotation_json")

    return _present_for_user(annotation_json_service, context.annotation, request.user)


def _present_for_user(service, annotation, user):
    annotation_json = service.present_for_user(annotation, user)

    annotation_json["moderation_status"] = (
        annotation.moderation_status.value
        if annotation.moderation_status
        else annotation.ModerationStatus.APPROVED.value
    )

    return annotation_json
