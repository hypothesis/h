from h.interfaces import IGroupService
from h.services.annotation_json_presentation.service import (
    AnnotationJSONPresentationService,
)


def annotation_json_presentation_service_factory(_context, request):
    group_svc = request.find_service(IGroupService)
    links_svc = request.find_service(name="links")
    flag_svc = request.find_service(name="flag")
    flag_count_svc = request.find_service(name="flag_count")
    moderation_svc = request.find_service(name="annotation_moderation")
    user_svc = request.find_service(name="user")
    return AnnotationJSONPresentationService(
        session=request.db,
        user=request.user,
        group_svc=group_svc,
        links_svc=links_svc,
        flag_svc=flag_svc,
        flag_count_svc=flag_count_svc,
        moderation_svc=moderation_svc,
        user_svc=user_svc,
        has_permission=request.has_permission,
    )
