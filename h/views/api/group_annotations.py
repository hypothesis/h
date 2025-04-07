import logging

from h.schemas.pagination import PaginationQueryParamsSchema
from h.schemas.util import validate_query_params
from h.security import Permission
from h.services.annotation_read import AnnotationReadService
from h.traversal import GroupContext
from h.views.api.config import api_config
from h.views.api.helpers.json_payload import json_payload

log = logging.getLogger(__name__)


LIST_MEMBERS_API_CONFIG = {
    "versions": ["v1", "v2"],
    "route_name": "api.group_annotations",
    "request_method": "GET",
    "link_name": "group.annotations.read",
    "description": "Fetch a list of all annotations of a group",
    # "permission": Permission.Group.READ, TOOD # add permission
}


@api_config(request_param="page[number]", **LIST_MEMBERS_API_CONFIG)
def list_annotations(context: GroupContext, request):
    group = context.group
    params = validate_query_params(PaginationQueryParamsSchema(), request.params)
    page_number = params["page[number]"]
    page_size = params["page[size]"]
    offset = page_size * (page_number - 1)
    limit = page_size

    annotation_json_service = request.find_service(name="annotation_json")

    query = AnnotationReadService.annotation_search_query(groupid=group.pubid)

    total = request.db.execute(AnnotationReadService.count_query(query)).scalar_one()
    annotations = request.db.scalars(query.offset(offset).limit(limit))

    annotations_dicts = [
        annotation_json_service.present_for_user(annotation, request.user)
        for annotation in annotations
    ]

    return {"meta": {"page": {"total": total}}, "data": annotations_dicts}
