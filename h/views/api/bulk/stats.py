import json

from importlib_resources import files
from pyramid.response import Response

from h.schemas.base import JSONSchema
from h.security import Permission
from h.services.bulk_api.lms_stats import BulkLMSStatsService, CountsGroupBy
from h.views.api.config import api_config


class AssignmentStatsSchema(JSONSchema):
    _SCHEMA_FILE = files("h.views.api.bulk") / "annotation_counts.json"
    schema_version = 7
    schema = json.loads(_SCHEMA_FILE.read_text(encoding="utf-8"))


@api_config(
    versions=["v1", "v2"],
    route_name="api.bulk.lms.annotations",
    request_method="POST",
    description="Retrieve annotations for LMS metrics",
    link_name="bulk.lms.annotations",
    subtype="x-ndjson",
    permission=Permission.API.BULK_ACTION,
)
def get_annotation_counts(request):
    data = AssignmentStatsSchema().validate(request.json)
    query_filter = data["filter"]

    stats = request.find_service(BulkLMSStatsService).get_annotation_counts(
        group_by=CountsGroupBy[data["group_by"].upper()],
        groups=query_filter["groups"],
        assignment_ids=query_filter.get("assignment_ids"),
        h_userids=query_filter.get("h_userids"),
    )

    return Response(
        json=[
            {
                "assignment_id": row.assignment_id,
                "userid": row.userid,
                "display_name": row.display_name,
                "annotations": row.annotations,
                "replies": row.replies,
                "page_notes": row.page_notes,
                "last_activity": row.last_activity.isoformat(),
            }
            for row in stats
        ],
        status=200,
        content_type="application/x-ndjson",
    )
