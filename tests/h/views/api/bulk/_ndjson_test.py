import json

import pytest
from pyramid.response import Response

from h.views.api.bulk._ndjson import get_ndjson_response


class TestGetNDJSONResponse:
    def test_it_formats_responses_correctly(self):
        return_values = [{"id": id_} for id_ in range(3)]

        result = get_ndjson_response(return_values)

        assert isinstance(result, Response)
        assert result.status == "200 OK"
        assert result.content_type == "application/x-ndjson"

        lines = result.body.decode("utf-8").split("\n")
        lines = [json.loads(line) for line in lines if line]
        assert lines == return_values

    def test_it_with_zero_items(self):
        result = get_ndjson_response([])

        assert not result.body.decode("utf-8")

    def test_it_returns_204_if_no_content_is_to_be_returned(self):
        result = get_ndjson_response(None)

        assert result.status == "204 No Content"

    def test_it_captures_initial_errors(self):
        def failing_method(fail=True):
            if fail:
                raise ValueError("Oh no!")

            yield 1  # pragma: nocover

        with pytest.raises(ValueError):
            get_ndjson_response(failing_method())
