from h.models import Annotation
from h.schemas.pagination import PaginationQueryParamsSchema
from h.schemas.util import validate_query_params
from h.security import Permission
from h.services.annotation_read import AnnotationReadService
from h.traversal import GroupContext
from h.views.api.config import api_config


@api_config(
    versions=["v1", "v2"],
    route_name="api.group_annotations",
    request_method="GET",
    link_name="group.annotations.read",
    description="Fetch a list of all annotations of a group",
    permission=Permission.Group.MODERATE,
    request_param="page[number]",
)
def list_annotations(context: GroupContext, request):
    group = context.group
    params = validate_query_params(PaginationQueryParamsSchema(), request.params)
    page_number = params["page[number]"]
    page_size = params["page[size]"]
    offset = page_size * (page_number - 1)
    limit = page_size

    annotation_json_service = request.find_service(name="annotation_json")

    moderation_status_filter = (
        Annotation.ModerationStatus(request.params.get("moderation_status").upper())
        if request.params.get("moderation_status")
        else None
    )
    query = AnnotationReadService.annotation_search_query(
        groupid=group.pubid,
        include_private=False,
        moderation_status=moderation_status_filter,
    )

    total = request.db.execute(AnnotationReadService.count_query(query)).scalar_one()
    annotations = request.db.scalars(
        query.order_by(Annotation.created.desc()).offset(offset).limit(limit)
    )

    annotations_dicts = [
        annotation_json_service.present_for_user(annotation, request.user)
        for annotation in annotations
    ]

    return {"meta": {"page": {"total": total}}, "data": annotations_dicts}
