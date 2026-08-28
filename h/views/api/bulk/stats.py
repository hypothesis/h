import json
from datetime import UTC, datetime

from importlib_resources import files
from pyramid.response import Response

from h.schemas.base import JSONSchema, ValidationError
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


def _isoformat(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _serialize(row) -> dict:
    counts = {
        "assignment_id": row.assignment_id,
        "userid": row.userid,
        "display_name": row.display_name,
        "annotations": row.annotations,
        "replies": row.replies,
        "page_notes": row.page_notes,
        "last_activity": _isoformat(row.last_activity),
    }

    if row.phase is None:
        return counts

    # One row per grading phase, with the boundary that closes it. A null
    # `ends_at` means the boundary isn't known yet: an unrevealed checkpoint,
    # or an assignment with no due date.
    return counts | {"phase": row.phase, "ends_at": _isoformat(row.ends_at)}


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

    try:
        stats = service.get_annotation_counts(
            group_by=CountsGroupBy[data["group_by"].upper()],
            groups=query_filter["groups"],
            assignment_ids=query_filter.get("assignment_ids"),
            h_userids=query_filter.get("h_userids"),
            document_uri=document_uri,
            due_date=_parse_due_date(due_date),
        )
    except ValueError as err:
        # A 400 even if the schema and the service ever disagree.
        raise ValidationError(str(err)) from err
    return Response(
        json=[_serialize(row) for row in stats],
        status=200,
        content_type="application/x-ndjson",
    )
