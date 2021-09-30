from h.services.annotation_json_presentation.service import (
    AnnotationJSONPresentationService,
)


def annotation_json_presentation_service_factory(_context, request):
    return AnnotationJSONPresentationService(
        session=request.db,
        # Services
        links_service=request.find_service(name="links"),
        flag_service=request.find_service(name="flag"),
        user_service=request.find_service(name="user"),
    )
