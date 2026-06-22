import json

from importlib_resources import files
from pyramid.response import Response

from h.schemas.base import JSONSchema
from h.security import Permission
from h.services.checkpoint import CheckpointService
from h.views.api.config import api_config


class BulkCheckpointSchema(JSONSchema):
    _SCHEMA_FILE = files("h.views.api.bulk") / "checkpoint_schema.json"
    schema_version = 7
    schema = json.loads(_SCHEMA_FILE.read_text(encoding="utf-8"))


@api_config(
    versions=["v1", "v2"],
    route_name="api.bulk.checkpoint",
    request_method="POST",
    link_name="bulk.checkpoint",
    description="Upsert checkpoints for hide and reveal",
    permission=Permission.API.BULK_ACTION,
)
def upsert_checkpoints(request):
    data = BulkCheckpointSchema().validate(request.json)
    authority = data["authority"]

    checkpoint_service = request.find_service(CheckpointService)

    if instructor_username := data.get("instructor_username"):
        # Mark the instructor role in all groups included in this request,
        # since a single sync can cover multiple groups (e.g. several course sections).
        checkpoint_service.set_instructor_role(
            authority=authority,
            username=instructor_username,
            group_authority_provided_ids=[
                item["group_authority_provided_id"]
                for item in data["checkpoints"]
            ],
        )

    results = []
    for item in data["checkpoints"]:
        checkpoint = checkpoint_service.upsert_checkpoint(
            authority=authority,
            group_authority_provided_id=item["group_authority_provided_id"],
            document_uri=item["document_uri"],
            reveal_date=item.get("reveal_date"),
        )
        results.append(
            {
                "group_authority_provided_id": item["group_authority_provided_id"],
                "document_uri": item["document_uri"],
                "created": checkpoint is not None,
            }
        )

    return Response(json=results, status=200)
