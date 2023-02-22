import json

from faker.factory import Factory
from importlib_resources import files

from h.schemas.base import JSONSchema
from h.security import Permission
from h.views.api.bulk._ndjson import get_ndjson_response
from h.views.api.config import api_config


class BulkAnnotationSchema(JSONSchema):
    _SCHEMA_FILE = files("h.views.api.bulk") / "annotation_schema.json"

    schema_version = 7
    schema = json.loads(_SCHEMA_FILE.read_text(encoding="utf-8"))


@api_config(
    versions=["v1", "v2"],
    route_name="api.bulk.annotation",
    request_method="POST",
    link_name="bulk.annotation",
    description="Retrieve a large number of annotations in one go",
    subtype="x-ndjson",
    permission=Permission.API.BULK_ACTION,
)
def bulk_annotation(request):
    """Retrieve a large number of annotations at once for LMS."""

    # Once this has been applied, we know everything else is safe to use
    # without checking any further
    data = BulkAnnotationSchema().validate(request.json)

    query_filter = {"limit": data["filter"]["limit"]}

    # Currently we are just faking as many rows as the user asks for in `limit`
    def get_rows(count):
        faker = Factory.create()

        for _ in range(count):
            yield {
                # pylint: disable=no-member
                "group": {"authority_provided_id": faker.hexify("^" * 40)},
                "author": {"username": faker.hexify("^" * 30)},
            }

    return get_ndjson_response(get_rows(query_filter["limit"]))
