from h.services.annotation_json_presentation.service import (
    AnnotationJSONPresentationService,
)


def annotation_json_presentation_service_factory(_context, request):
    return AnnotationJSONPresentationService(
        session=request.db,
        user=request.user,
        has_permission=request.has_permission,
        # Services
        links_svc=request.find_service(name="links"),
        flag_svc=request.find_service(name="flag"),
        flag_count_svc=request.find_service(name="flag_count"),
        user_svc=request.find_service(name="user"),
    )
