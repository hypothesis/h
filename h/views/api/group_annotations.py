from h.models import Annotation
from h.models.annotation import ModerationStatus
from h.schemas.api.group import FilterGroupAnnotationsSchema
from h.schemas.pagination import CursorPagination
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
)
def list_annotations(context: GroupContext, request):
    assert context.group is not None, "Group is required"  # noqa: S101

    pagination = CursorPagination.from_params(request.params)
    params = validate_query_params(FilterGroupAnnotationsSchema(), request.params)

    group = context.group
    annotation_json_service = request.find_service(name="annotation_json")

    moderation_status_filter = (
        ModerationStatus(params["moderation_status"])
        if params.get("moderation_status")
        else None
    )
    query = AnnotationReadService.annotation_search_query(
        groupid=group.pubid, moderation_status=moderation_status_filter
    )

    total = request.db.execute(AnnotationReadService.count_query(query)).scalar_one()

    query = query.order_by(Annotation.created.desc()).limit(pagination.size)

    if pagination.after:
        query = query.where(Annotation.created < pagination.after)

    annotations = request.db.scalars(query)

    annotations_dicts = [
        annotation_json_service.present_for_user(annotation, request.user)
        for annotation in annotations
    ]

    return {"meta": {"page": {"total": total}}, "data": annotations_dicts}
