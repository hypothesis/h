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


class BulkCheckpointRevealSchema(JSONSchema):
    _SCHEMA_FILE = files("h.views.api.bulk") / "checkpoint_reveal_schema.json"
    schema_version = 7
    schema = json.loads(_SCHEMA_FILE.read_text(encoding="utf-8"))


@api_config(
    versions=["v1", "v2"],
    route_name="api.bulk.checkpoint",
    request_method="POST",
    link_name="bulk.checkpoint",
    description="Upsert checkpoints",
    permission=Permission.API.BULK_ACTION,
)
def upsert_checkpoints(request):
    data = BulkCheckpointSchema().validate(request.json)
    authority = data["authority"]

    checkpoint_service = request.find_service(CheckpointService)

    group_authority_provided_ids = [
        item["group_authority_provided_id"] for item in data["checkpoints"]
    ]

    if user_data := data.get("user"):
        checkpoint_service.set_user_role(
            authority=authority,
            username=user_data["username"],
            role=user_data["role"],
            group_authority_provided_ids=group_authority_provided_ids,
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


@api_config(
    versions=["v1", "v2"],
    route_name="api.bulk.checkpoint.reveal",
    request_method="POST",
    link_name="bulk.checkpoint.reveal",
    description="Reveal checkpoints, making annotations visible immediately",
    permission=Permission.API.BULK_ACTION,
)
def reveal_checkpoints(request):
    data = BulkCheckpointRevealSchema().validate(request.json)
    authority = data["authority"]

    checkpoint_service = request.find_service(CheckpointService)

    results = []
    for item in data["checkpoints"]:
        checkpoint = checkpoint_service.reveal_checkpoints(
            authority=authority,
            group_authority_provided_id=item["group_authority_provided_id"],
            document_uri=item["document_uri"],
        )
        results.append(
            {
                "group_authority_provided_id": item["group_authority_provided_id"],
                "document_uri": item["document_uri"],
                "revealed": checkpoint is not None,
            }
        )

    return Response(json=results, status=200)
