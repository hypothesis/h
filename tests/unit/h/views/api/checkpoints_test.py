from datetime import datetime
from unittest import mock

import pytest
from pyramid.httpexceptions import HTTPNotFound

from h.schemas import ValidationError
from h.services.checkpoint import CheckpointService, GroupNotFoundError
from h.views.api.checkpoints import upsert
from h.views.api.exceptions import PayloadError


@pytest.mark.usefixtures("with_auth_client")
class TestUpsert:
    def test_it(self, pyramid_request, checkpoint_service, auth_client):
        pyramid_request.json_body = {
            "authority_provided_id": "apid",
            "document_url": "http://example.com/page",
            "reveal_date": "2026-07-01T00:00:00",
        }

        result = upsert(pyramid_request)

        checkpoint_service.upsert.assert_called_once_with(
            authority=auth_client.authority,
            authority_provided_id="apid",
            document_url="http://example.com/page",
            reveal_date=datetime(2026, 7, 1),  # noqa: DTZ001
        )
        # The response reflects the checkpoint the service returned.
        assert result == {"id": 123, "reveal_date": "2026-12-25T00:00:00"}

    def test_it_passes_none_when_reveal_date_is_null(
        self, pyramid_request, checkpoint_service
    ):
        pyramid_request.json_body = {
            "authority_provided_id": "apid",
            "document_url": "http://example.com/page",
            "reveal_date": None,
        }

        upsert(pyramid_request)

        assert checkpoint_service.upsert.call_args.kwargs["reveal_date"] is None

    def test_it_passes_none_when_reveal_date_is_absent(
        self, pyramid_request, checkpoint_service
    ):
        pyramid_request.json_body = {
            "authority_provided_id": "apid",
            "document_url": "http://example.com/page",
        }

        upsert(pyramid_request)

        assert checkpoint_service.upsert.call_args.kwargs["reveal_date"] is None

    def test_it_converts_a_tz_aware_reveal_date_to_naive_utc(
        self, pyramid_request, checkpoint_service
    ):
        pyramid_request.json_body = {
            "authority_provided_id": "apid",
            "document_url": "http://example.com/page",
            "reveal_date": "2026-07-01T12:00:00+02:00",
        }

        upsert(pyramid_request)

        expected = datetime(2026, 7, 1, 10, 0, 0)  # noqa: DTZ001
        assert checkpoint_service.upsert.call_args.kwargs["reveal_date"] == expected

    def test_it_returns_null_when_the_checkpoint_has_no_reveal_date(
        self, pyramid_request, checkpoint_service
    ):
        checkpoint_service.upsert.return_value = mock.Mock(id=5, reveal_date=None)
        pyramid_request.json_body = {
            "authority_provided_id": "apid",
            "document_url": "http://example.com/page",
        }

        result = upsert(pyramid_request)

        assert result == {"id": 5, "reveal_date": None}

    def test_it_raises_for_an_invalid_reveal_date(self, pyramid_request):
        pyramid_request.json_body = {
            "authority_provided_id": "apid",
            "document_url": "http://example.com/page",
            "reveal_date": "not-a-date",
        }

        with pytest.raises(ValidationError):
            upsert(pyramid_request)

    def test_it_raises_HTTPNotFound_when_the_group_is_not_found(
        self, pyramid_request, checkpoint_service
    ):
        checkpoint_service.upsert.side_effect = GroupNotFoundError("apid")
        pyramid_request.json_body = {
            "authority_provided_id": "apid",
            "document_url": "http://example.com/page",
        }

        with pytest.raises(HTTPNotFound):
            upsert(pyramid_request)

    def test_it_raises_when_a_required_field_is_missing(self, pyramid_request):
        pyramid_request.json_body = {"authority_provided_id": "apid"}

        with pytest.raises(ValidationError):
            upsert(pyramid_request)

    def test_it_raises_for_an_invalid_json_body(self, pyramid_request):
        type(pyramid_request).json_body = mock.PropertyMock(side_effect=ValueError())

        with pytest.raises(PayloadError):
            upsert(pyramid_request)

    @pytest.fixture
    def checkpoint_service(self, mock_service):
        service = mock_service(CheckpointService)
        service.upsert.return_value = mock.Mock(
            id=123,
            reveal_date=datetime(2026, 12, 25),  # noqa: DTZ001
        )
        return service
