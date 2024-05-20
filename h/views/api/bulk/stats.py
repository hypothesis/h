import json

from importlib_resources import files
from pyramid.response import Response

from h.schemas.base import JSONSchema
from h.security import Permission
from h.services.bulk_api import BulkLMSStatsService
from h.views.api.config import api_config


class AssignmentStatsSchema(JSONSchema):
    _SCHEMA_FILE = files("h.views.api.bulk") / "stats_assignment.json"
    schema_version = 7
    schema = json.loads(_SCHEMA_FILE.read_text(encoding="utf-8"))


class CourseStatsSchema(JSONSchema):
    _SCHEMA_FILE = files("h.views.api.bulk") / "stats_course.json"
    schema_version = 7
    schema = json.loads(_SCHEMA_FILE.read_text(encoding="utf-8"))


@api_config(
    versions=["v1", "v2"],
    route_name="api.bulk.stats.users",
    request_method="POST",
    description="Retrieve stats grouped by user",
    link_name="bulk.stats.assignment",
    subtype="x-ndjson",
    permission=Permission.API.BULK_ACTION,
)
def get_counts_by_user(request):
    data = AssignmentStatsSchema().validate(request.json)
    query_filter = data["filter"]

    stats = request.find_service(BulkLMSStatsService).get_counts_by_user(
        groups=query_filter["groups"],
        assignment_id=query_filter["assignment_id"],
    )

    return Response(
        json=[
            {
                "display_name": row.display_name,
                "userid": row.userid,
                "annotations": row.annotations,
                "replies": row.replies,
                "last_activity": row.last_activity.isoformat(),
            }
            for row in stats
        ],
        status=200,
        content_type="application/x-ndjson",
    )


@api_config(
    versions=["v1", "v2"],
    route_name="api.bulk.stats.assignments",
    request_method="POST",
    description="Retrieve stats grouped by assignment",
    link_name="bulk.stats.course",
    subtype="x-ndjson",
    permission=Permission.API.BULK_ACTION,
)
def get_counts_by_assignment(request):
    data = CourseStatsSchema().validate(request.json)
    query_filter = data["filter"]

    stats = request.find_service(BulkLMSStatsService).get_counts_by_assignment(
        groups=query_filter["groups"],
    )

    return Response(
        json=[
            {
                "assignment_id": row.assignment_id,
                "annotations": row.annotations,
                "replies": row.replies,
                "last_activity": row.last_activity.isoformat(),
            }
            for row in stats
        ],
        status=200,
        content_type="application/x-ndjson",
    )
