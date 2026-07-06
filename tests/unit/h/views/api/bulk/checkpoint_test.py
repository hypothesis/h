from datetime import datetime
from unittest.mock import Mock

import pytest

from h.schemas import ValidationError
from h.services.checkpoint import CheckpointService
from h.views.api.bulk.checkpoint import (
    BulkCheckpointRevealSchema,
    BulkCheckpointSchema,
    reveal_checkpoints,
    upsert_checkpoints,
)


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
            "user": {"username": "teacher", "role": "instructor"},
            "checkpoints": [
                {
                    "group_authority_provided_id": "group1",
                    "document_uri": "http://example.com/1",
                },
                {
                    "group_authority_provided_id": "group2",
                    "document_uri": "http://example.com/2",
                },
            ],
        }

        response = upsert_checkpoints(pyramid_request)

        checkpoint_service.set_user_role.assert_called_once_with(
            authority=pyramid_request.identity.auth_client.authority,
            username="teacher",
            role="instructor",
            group_authority_provided_ids=["group1", "group2"],
        )
        checkpoint_service.upsert_checkpoint.assert_any_call(
            authority=pyramid_request.identity.auth_client.authority,
            group_authority_provided_id="group1",
            document_uri="http://example.com/1",
        )
        checkpoint_service.upsert_checkpoint.assert_any_call(
            authority=pyramid_request.identity.auth_client.authority,
            group_authority_provided_id="group2",
            document_uri="http://example.com/2",
        )
        assert response.status_code == 200
        assert response.json == [
            {
                "group_authority_provided_id": "group1",
                "document_uri": "http://example.com/1",
                "created": True,
                "revealed": False,
                "reveal_date": None,
            },
            {
                "group_authority_provided_id": "group2",
                "document_uri": "http://example.com/2",
                "created": True,
                "revealed": False,
                "reveal_date": None,
            },
        ]

    def test_it_does_not_set_role_without_user(
        self, pyramid_request, checkpoint_service
    ):
        pyramid_request.json = {
            "checkpoints": [
                {
                    "group_authority_provided_id": "group1",
                    "document_uri": "http://example.com/1",
                },
            ],
        }

        upsert_checkpoints(pyramid_request)

        checkpoint_service.set_user_role.assert_not_called()

    def test_it_sets_student_role(self, pyramid_request, checkpoint_service):
        pyramid_request.json = {
            "user": {"username": "student1", "role": "student"},
            "checkpoints": [
                {
                    "group_authority_provided_id": "group1",
                    "document_uri": "http://example.com/1",
                },
            ],
        }

        upsert_checkpoints(pyramid_request)

        checkpoint_service.set_user_role.assert_called_once_with(
            authority=pyramid_request.identity.auth_client.authority,
            username="student1",
            role="student",
            group_authority_provided_ids=["group1"],
        )

    def test_it_reports_unresolved_items_as_not_created(
        self, pyramid_request, checkpoint_service
    ):
        checkpoint_service.upsert_checkpoint.return_value = None
        pyramid_request.json = {
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
                "revealed": False,
                "reveal_date": None,
            },
        ]

    def test_it_includes_reveal_date(self, pyramid_request, checkpoint_service):
        checkpoint_service.upsert_checkpoint.return_value = Mock(
            reveal_date=datetime(2020, 1, 1, 10, 0, 0)  # noqa: DTZ001
        )
        pyramid_request.json = {
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
                "created": True,
                "revealed": True,
                "reveal_date": "2020-01-01T10:00:00",
            },
        ]

    def test_it_raises_with_invalid_request(self, pyramid_request):
        pyramid_request.json = {"nope": True}

        with pytest.raises(ValidationError):
            upsert_checkpoints(pyramid_request)

    def test_it_rejects_authority_in_body(self, pyramid_request):
        pyramid_request.json = {
            "authority": "attacker.hypothes.is",
            "checkpoints": [
                {
                    "group_authority_provided_id": "group1",
                    "document_uri": "http://example.com/1",
                },
            ],
        }

        with pytest.raises(ValidationError):
            upsert_checkpoints(pyramid_request)

    @pytest.fixture
    def checkpoint_service(self, mock_service):
        service = mock_service(CheckpointService)
        service.upsert_checkpoint.return_value.reveal_date = None
        return service


class TestBulkCheckpointRevealSchema:
    def test_it_is_a_valid_schema(self, schema):
        assert not schema.validator.check_schema(schema.schema)

    @pytest.fixture
    def schema(self):
        return BulkCheckpointRevealSchema()


@pytest.mark.usefixtures("checkpoint_service", "with_auth_client")
class TestRevealCheckpoints:
    def test_it(self, pyramid_request, checkpoint_service):
        pyramid_request.json = {
            "checkpoints": [
                {
                    "group_authority_provided_id": "group1",
                    "document_uri": "http://example.com/1",
                },
            ],
        }

        response = reveal_checkpoints(pyramid_request)

        checkpoint_service.reveal_checkpoint.assert_called_once_with(
            authority=pyramid_request.identity.auth_client.authority,
            group_authority_provided_id="group1",
            document_uri="http://example.com/1",
        )
        assert response.status_code == 200
        assert response.json == [
            {
                "group_authority_provided_id": "group1",
                "document_uri": "http://example.com/1",
                "revealed": True,
                "reveal_date": None,
            },
        ]

    def test_it_reports_unresolved_items(self, pyramid_request, checkpoint_service):
        checkpoint_service.reveal_checkpoint.return_value = None
        pyramid_request.json = {
            "checkpoints": [
                {
                    "group_authority_provided_id": "group1",
                    "document_uri": "http://example.com/1",
                },
            ],
        }

        response = reveal_checkpoints(pyramid_request)

        assert response.json == [
            {
                "group_authority_provided_id": "group1",
                "document_uri": "http://example.com/1",
                "revealed": False,
                "reveal_date": None,
            },
        ]

    def test_it_rejects_authority_in_body(self, pyramid_request):
        pyramid_request.json = {
            "authority": "attacker.hypothes.is",
            "checkpoints": [
                {
                    "group_authority_provided_id": "group1",
                    "document_uri": "http://example.com/1",
                },
            ],
        }

        with pytest.raises(ValidationError):
            reveal_checkpoints(pyramid_request)

    @pytest.fixture
    def checkpoint_service(self, mock_service):
        service = mock_service(CheckpointService)
        service.reveal_checkpoint.return_value.reveal_date = None
        return service
