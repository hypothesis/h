from h.services.annotation_json_presentation.service import (
    AnnotationJSONPresentationService,
)


def annotation_json_presentation_service_factory(_context, request):
    return AnnotationJSONPresentationService(
        session=request.db,
        # Services
        links_svc=request.find_service(name="links"),
        flag_svc=request.find_service(name="flag"),
        user_svc=request.find_service(name="user"),
    )
