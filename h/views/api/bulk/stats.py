import json

from importlib_resources import files

from h.schemas.base import JSONSchema
from h.security import Permission
from h.services.bulk_api import BulkLMSStatsService
from h.views.api.bulk._ndjson import get_ndjson_response
from h.views.api.config import api_config


class AssignmentStatsSchema(JSONSchema):
    _SCHEMA_FILE = files("h.views.api.bulk") / "stats_assignment.json"
    schema_version = 7
    schema = json.loads(_SCHEMA_FILE.read_text(encoding="utf-8"))


@api_config(
    versions=["v1", "v2"],
    route_name="api.bulk.stats.assignment",
    request_method="POST",
    description="Retrieve stats for a single LMS assignment",
    link_name="bulk.stats.assignment",
    subtype="x-ndjson",
    permission=Permission.API.BULK_ACTION,
)
def assignment(request):
    data = AssignmentStatsSchema().validate(request.json)
    query_filter = data["filter"]

    stats = request.find_service(BulkLMSStatsService).assignment_stats(
        groups=query_filter["groups"],
        assignment_id=query_filter["assignment_id"],
    )
    return get_ndjson_response(
        [
            {
                "display_name": row.display_name,
                "annotations": row.annotations,
                "replies": row.replies,
                "last_activity": row.last_activity.isoformat(),
            }
            for row in stats
        ],
        stream=False,
    )
