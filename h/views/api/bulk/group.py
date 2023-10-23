import json

from importlib_resources import files

from h.schemas import ValidationError
from h.schemas.base import JSONSchema
from h.security import Permission
from h.services.bulk_api import BadDateFilter, BulkGroupService
from h.views.api.bulk._ndjson import get_ndjson_response
from h.views.api.config import api_config


class BulkGroupSchema(JSONSchema):
    _SCHEMA_FILE = files("h.views.api.bulk") / "group_schema.json"

    schema_version = 7
    schema = json.loads(_SCHEMA_FILE.read_text(encoding="utf-8"))


@api_config(
    versions=["v1", "v2"],
    route_name="api.bulk.group",
    request_method="POST",
    link_name="bulk.group",
    description="Retrieve a large number of groups in one go",
    subtype="x-ndjson",
    permission=Permission.API.BULK_ACTION,
)
def bulk_group(request):
    data = BulkGroupSchema().validate(request.json)
    query_filter = data["filter"]

    try:
        groups = request.find_service(BulkGroupService).group_search(
            groups=query_filter["groups"],
            annotations_created=query_filter["annotations_created"],
        )

    except BadDateFilter as err:
        raise ValidationError(str(err)) from err

    return get_ndjson_response(
        [{"authority_provided_id": group.authority_provided_id} for group in groups]
    )
