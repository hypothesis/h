import pytest

from h.schemas import ValidationError
from h.services.checkpoint import CheckpointService
from h.views.api.bulk.checkpoint import BulkCheckpointSchema, upsert_checkpoints


class TestBulkCheckpointSchema:
    def test_it_is_a_valid_schema(self, schema):
        # Basic self-check that this is a valid JSON schema.
        assert not schema.validator.check_schema(schema.schema)

    @pytest.fixture
    def schema(self):
        return BulkCheckpointSchema()


@pytest.mark.usefixtures("checkpoint_service", "with_auth_client")
class TestUpsertCheckpoints:
    def test_it(self, pyramid_request, checkpoint_service):
        pyramid_request.json = {
            "authority": "lms.hypothes.is",
            "instructor_username": "teacher",
            "checkpoints": [
                {
                    "group_authority_provided_id": "group1",
                    "document_uri": "http://example.com/1",
                    "reveal_date": "2026-07-01T10:00:00",
                },
                {
                    "group_authority_provided_id": "group2",
                    "document_uri": "http://example.com/2",
                },
            ],
        }

        response = upsert_checkpoints(pyramid_request)

        checkpoint_service.set_instructor_role.assert_called_once_with(
            authority="lms.hypothes.is",
            username="teacher",
            group_authority_provided_ids=["group1", "group2"],
        )
        checkpoint_service.upsert_checkpoint.assert_any_call(
            authority="lms.hypothes.is",
            group_authority_provided_id="group1",
            document_uri="http://example.com/1",
            reveal_date="2026-07-01T10:00:00",
        )
        checkpoint_service.upsert_checkpoint.assert_any_call(
            authority="lms.hypothes.is",
            group_authority_provided_id="group2",
            document_uri="http://example.com/2",
            reveal_date=None,
        )
        assert response.status_code == 200
        assert response.json == [
            {
                "group_authority_provided_id": "group1",
                "document_uri": "http://example.com/1",
                "created": True,
            },
            {
                "group_authority_provided_id": "group2",
                "document_uri": "http://example.com/2",
                "created": True,
            },
        ]

    def test_it_does_not_set_instructor_role_without_an_instructor(
        self, pyramid_request, checkpoint_service
    ):
        pyramid_request.json = {
            "authority": "lms.hypothes.is",
            "checkpoints": [
                {
                    "group_authority_provided_id": "group1",
                    "document_uri": "http://example.com/1",
                },
            ],
        }

        upsert_checkpoints(pyramid_request)

        checkpoint_service.set_instructor_role.assert_not_called()

    def test_it_reports_unresolved_items_as_not_created(
        self, pyramid_request, checkpoint_service
    ):
        checkpoint_service.upsert_checkpoint.return_value = None
        pyramid_request.json = {
            "authority": "lms.hypothes.is",
            "checkpoints": [
                {
                    "group_authority_provided_id": "group1",
                    "document_uri": "http://example.com/1",
                },
            ],
        }

        response = upsert_checkpoints(pyramid_request)

        assert response.json == [
            {
                "group_authority_provided_id": "group1",
                "document_uri": "http://example.com/1",
                "created": False,
            },
        ]

    def test_it_raises_with_invalid_request(self, pyramid_request):
        pyramid_request.json = {"nope": True}

        with pytest.raises(ValidationError):
            upsert_checkpoints(pyramid_request)

    @pytest.fixture
    def checkpoint_service(self, mock_service):
        return mock_service(CheckpointService)
