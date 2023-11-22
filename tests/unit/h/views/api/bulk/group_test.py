import pytest
from h_matchers import Any

from h.schemas import ValidationError
from h.services.bulk_api.exceptions import BadDateFilter
from h.services.bulk_api.group import BulkGroup
from h.views.api.bulk.group import BulkGroupSchema, bulk_group


class TestBulkGroupSchema:
    def test_it_is_a_valid_schema(self, schema):
        # Extremely basic self checking that this is a valid JSON schema
        assert not schema.validator.check_schema(schema.schema)

    def test_examples_are_valid(self, schema):
        for example in schema.schema["examples"]:
            schema.validate(example)

    @pytest.fixture
    def schema(self):
        return BulkGroupSchema()


@pytest.mark.usefixtures("bulk_group_service", "with_auth_client")
class TestBulkGroup:
    def test_it(
        self,
        pyramid_request,
        valid_request,
        bulk_group_service,
        get_ndjson_response,
    ):
        bulk_group_service.group_search.return_value = [
            BulkGroup(
                authority_provided_id=f"AUTHORITY_PROVIDED_ID_{i}",
            )
            for i in range(3)
        ]

        response = bulk_group(pyramid_request)

        bulk_group_service.group_search.assert_called_once_with(
            groups=valid_request["filter"]["groups"],
            annotations_created=valid_request["filter"]["annotations_created"],
        )

        return_data = [
            {"authority_provided_id": f"AUTHORITY_PROVIDED_ID_{i}"} for i in range(3)
        ]
        get_ndjson_response.assert_called_once_with(
            Any.iterable.containing(return_data).only()
        )

        assert response == get_ndjson_response.return_value

    def test_it_raises_with_invalid_request(self, pyramid_request):
        pyramid_request.json = {"nope": True}

        with pytest.raises(ValidationError):
            bulk_group(pyramid_request)

    @pytest.mark.usefixtures("valid_request")
    def test_it_raises_with_errors_from_the_bulk_service(
        self, pyramid_request, bulk_group_service
    ):
        bulk_group_service.group_search.side_effect = BadDateFilter

        with pytest.raises(ValidationError):
            bulk_group(pyramid_request)

    @pytest.fixture
    def valid_request(self, pyramid_request):
        pyramid_request.json = {
            "filter": {
                "groups": ["3a022b6c146dfd9df4ea8662178eac"],
                "annotations_created": {
                    "gt": "2018-11-13T20:20:39+00:00",
                    "lte": "2018-11-13T20:20:39+00:00",
                },
            },
        }

        return pyramid_request.json

    @pytest.fixture(autouse=True)
    def get_ndjson_response(self, patch):
        return patch("h.views.api.bulk.group.get_ndjson_response")
