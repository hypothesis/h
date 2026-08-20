import json
from datetime import UTC, datetime

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


def _parse_due_date(due_date: str | None) -> datetime | None:
    """Normalise an ISO due date to the naive UTC the DB stores.

    `AnnotationSlim.created` is naive UTC, so an offset-aware bound would leave
    the comparison up to the database session's timezone. The schema's date-time
    format requires an offset, so there is no local time to guess at here.
    """
    if not due_date:
        return None

    return datetime.fromisoformat(due_date).astimezone(UTC).replace(tzinfo=None)


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
    document_uri = query_filter.get("document_uri")
    due_date = query_filter.get("due_date")
    service = request.find_service(BulkLMSStatsService)

    stats = service.get_annotation_counts(
        group_by=CountsGroupBy[data["group_by"].upper()],
        groups=query_filter["groups"],
        assignment_ids=query_filter.get("assignment_ids"),
        h_userids=query_filter.get("h_userids"),
        document_uri=document_uri,
        due_date=_parse_due_date(due_date),
    )
    checkpoint_revealed, checkpoint_reveal_date = (
        service.get_checkpoint_state(query_filter["groups"], document_uri)
        if document_uri
        else (None, None)
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
                **(
                    {
                        "checkpoint_annotations": row.checkpoint_annotations,
                        "checkpoint_replies": row.checkpoint_replies,
                        "checkpoint_page_notes": row.checkpoint_page_notes,
                        "checkpoint_last_activity": (
                            row.checkpoint_last_activity.isoformat()
                            if row.checkpoint_last_activity
                            else None
                        ),
                        "checkpoint_revealed": checkpoint_revealed,
                        "checkpoint_reveal_date": (
                            checkpoint_reveal_date.isoformat()
                            if checkpoint_reveal_date
                            else None
                        ),
                    }
                    if document_uri
                    else {}
                ),
            }
            for row in stats
        ],
        status=200,
        content_type="application/x-ndjson",
    )
