from h.services.annotation_json.service import AnnotationJSONService


def annotation_json_service_factory(_context, request):
    return AnnotationJSONService(
        session=request.db,
        # Services
        links_service=request.find_service(name="links"),
        flag_service=request.find_service(name="flag"),
        user_service=request.find_service(name="user"),
    )
