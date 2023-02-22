import pytest
from h_matchers import Any

from h.schemas import ValidationError
from h.views.api.bulk.annotation import BulkAnnotationSchema, bulk_annotation


class TestBulkAnnotationSchema:
    def test_it_is_a_valid_schema(self, schema):
        # Extremely basic self checking that this is a valid JSON schema
        assert not schema.validator.check_schema(schema.schema)

    def test_examples_are_valid(self, schema):
        for example in schema.schema["examples"]:
            schema.validate(example)

    @pytest.fixture
    def schema(self):
        return BulkAnnotationSchema()


class TestBulkAnnotation:
    def test_it_calls_bulk_api_correctly(
        self, pyramid_request, valid_request, get_ndjson_response
    ):
        valid_request["filter"]["limit"] = 10

        response = bulk_annotation(pyramid_request)

        get_ndjson_response.assert_called_once_with(
            Any.iterable.of_size(10).comprised_of(
                {
                    "group": {"authority_provided_id": Any.string()},
                    "author": {"username": Any.string()},
                }
            )
        )
        assert response == get_ndjson_response.return_value

    def test_it_raises_with_invalid_request(self, pyramid_request):
        pyramid_request.json = {"nope": True}

        with pytest.raises(ValidationError):
            bulk_annotation(pyramid_request)

    @pytest.fixture
    def valid_request(self, pyramid_request):
        pyramid_request.json = {
            "filter": {
                "limit": 2000,
                "audience": {"username": ["3a022b6c146dfd9df4ea8662178eac"]},
                "updated": {
                    "gt": "2018-11-13T20:20:39+00:00",
                    "lte": "2018-11-13T20:20:39+00:00",
                },
            },
            "fields": ["group.authority_provided_id", "author.username"],
        }

        return pyramid_request.json

    @pytest.fixture(autouse=True)
    def get_ndjson_response(self, patch):
        return patch("h.views.api.bulk.annotation.get_ndjson_response")
