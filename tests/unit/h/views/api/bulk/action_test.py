from io import BytesIO
from unittest.mock import create_autospec

import pytest

from h.views.api.bulk.action import bulk_action


@pytest.mark.usefixtures("with_auth_client")
class TestBulkAction:
    def test_it_calls_bulk_api_correctly(
        self, pyramid_request, BulkAPI, bulk_executor, get_ndjson_response
    ):
        response = bulk_action(pyramid_request)

        BulkAPI.from_byte_stream.assert_called_once_with(
            pyramid_request.body_file, executor=bulk_executor.return_value
        )

        bulk_executor.assert_called_once_with(
            pyramid_request.db, authority=pyramid_request.identity.auth_client.authority
        )
        get_ndjson_response.assert_called_once_with(
            BulkAPI.from_byte_stream.return_value
        )

        assert response == get_ndjson_response.return_value

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.body_file = create_autospec(BytesIO)

        return pyramid_request

    @pytest.fixture(autouse=True)
    def BulkAPI(self, patch):
        return patch("h.views.api.bulk.action.BulkAPI")

    @pytest.fixture(autouse=True)
    def get_ndjson_response(self, patch):
        return patch("h.views.api.bulk.action.get_ndjson_response")

    @pytest.fixture(autouse=True)
    def bulk_executor(self, patch):
        return patch("h.views.api.bulk.action.BulkExecutor")
