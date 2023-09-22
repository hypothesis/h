from pyramid.httpexceptions import HTTPNoContent

from h import events
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
