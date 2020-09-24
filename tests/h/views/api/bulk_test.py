import json
from io import BytesIO
from unittest.mock import create_autospec

import pytest
from h_api.exceptions import SchemaValidationError
from webob import Response

from h.views.api.bulk import bulk


class TestBulk:
    def test_it_calls_bulk_api_correctly(self, pyramid_request, BulkAPI, bulk_executor):
        bulk(pyramid_request)

        BulkAPI.from_byte_stream.assert_called_once_with(
            pyramid_request.body_file, executor=bulk_executor.return_value
        )

        bulk_executor.assert_called_once_with(pyramid_request.db)

    def test_it_formats_responses_correctly(self, pyramid_request, return_values):
        result = bulk(pyramid_request)

        assert isinstance(result, Response)
        assert result.status == "200 OK"
        assert result.content_type == "application/x-ndjson"

        lines = result.body.decode("utf-8").split("\n")
        lines = [json.loads(line) for line in lines if line]
        assert lines == return_values

    @pytest.mark.usefixtures("no_return_content")
    def test_it_returns_204_if_no_content_is_to_be_returned(self, pyramid_request):
        result = bulk(pyramid_request)

        assert result.status == "204 No Content"

    def test_it_raises_with_output_and_invalid_input(self, BulkAPI, pyramid_request):
        def bad_generator(*_, **__):
            raise SchemaValidationError([], "Bad!")
            # Looks like this doesn't do anything, but it turns this into a
            # generator. Unless the first item is retrieved the above is not
            # executed.
            yield {}

        BulkAPI.from_byte_stream.side_effect = bad_generator

        with pytest.raises(SchemaValidationError):
            bulk(pyramid_request)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.body_file = create_autospec(BytesIO)

        return pyramid_request

    @pytest.fixture
    def return_values(self):
        return [{f"row_{i}": "value"} for i in range(3)]

    @pytest.fixture(autouse=True)
    def BulkAPI(self, patch, return_values):
        BulkAPI = patch("h.views.api.bulk.BulkAPI")
        BulkAPI.from_byte_stream.return_value = (value for value in return_values)

        return BulkAPI

    @pytest.fixture
    def no_return_content(self, BulkAPI):
        BulkAPI.from_byte_stream.return_value = None

    @pytest.fixture(autouse=True)
    def bulk_executor(self, patch):
        return patch("h.views.api.bulk.BulkExecutor")
