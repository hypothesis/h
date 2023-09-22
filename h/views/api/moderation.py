from pyramid.httpexceptions import HTTPNoContent

from h.models import AnnotationModeration
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
def create(context, request):
    request.find_service(AnnotationModeration).create(context.annotation)
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
    request.find_service(AnnotationModeration).delete(context.annotation)
    return HTTPNoContent()
