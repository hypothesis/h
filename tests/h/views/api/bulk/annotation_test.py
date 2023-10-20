from unittest.mock import sentinel

import pytest
from h_matchers import Any

from h.schemas import ValidationError
from h.services.bulk_annotation import BadDateFilter, BulkAnnotation, service_factory
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


@pytest.mark.usefixtures("bulk_annotation_service", "with_auth_client")
class TestBulkAnnotation:
    def test_it(
        self,
        pyramid_request,
        valid_request,
        bulk_annotation_service,
        get_ndjson_response,
    ):
        bulk_annotation_service.annotation_search.return_value = [
            BulkAnnotation(
                username=f"USERNAME_{i}",
                authority_provided_id=f"AUTHORITY_PROVIDED_ID_{i}",
                metadata={"key": i},
            )
            for i in range(3)
        ]

        response = bulk_annotation(pyramid_request)

        bulk_annotation_service.annotation_search.assert_called_once_with(
            authority=pyramid_request.identity.auth_client.authority,
            audience=valid_request["filter"]["audience"],
            limit=valid_request["filter"]["limit"],
            created=valid_request["filter"]["created"],
        )

        return_data = [
            {
                "author": {"username": f"USERNAME_{i}"},
                "group": {"authority_provided_id": f"AUTHORITY_PROVIDED_ID_{i}"},
                "metadata": {"key": i},
            }
            for i in range(3)
        ]
        get_ndjson_response.assert_called_once_with(
            Any.iterable.containing(return_data).only()
        )

        assert response == get_ndjson_response.return_value

    def test_it_raises_with_invalid_request(self, pyramid_request):
        pyramid_request.json = {"nope": True}

        with pytest.raises(ValidationError):
            bulk_annotation(pyramid_request)

    @pytest.mark.usefixtures("valid_request")
    def test_it_raises_with_errors_from_the_bulk_service(
        self, pyramid_request, bulk_annotation_service
    ):
        bulk_annotation_service.annotation_search.side_effect = BadDateFilter

        with pytest.raises(ValidationError):
            bulk_annotation(pyramid_request)

    @pytest.fixture
    def valid_request(self, pyramid_request):
        pyramid_request.json = {
            "filter": {
                "limit": 2000,
                "audience": {"username": ["3a022b6c146dfd9df4ea8662178eac"]},
                "created": {
                    "gt": "2018-11-13T20:20:39+00:00",
                    "lte": "2018-11-13T20:20:39+00:00",
                },
            },
        }

        return pyramid_request.json

    @pytest.fixture(autouse=True)
    def get_ndjson_response(self, patch):
        return patch("h.views.api.bulk.annotation.get_ndjson_response")


class TestServiceFactory:
    def test_it(self, pyramid_request, BulkAnnotationService):
        svc = service_factory(sentinel.context, pyramid_request)

        BulkAnnotationService.assert_called_once_with(db_session=pyramid_request.db)
        assert svc == BulkAnnotationService.return_value

    @pytest.fixture
    def BulkAnnotationService(self, patch):
        return patch("h.services.bulk_annotation.BulkAnnotationService")
