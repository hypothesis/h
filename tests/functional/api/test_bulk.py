import json

import pytest
from h_matchers import Any

from h.h_api.bulk_api import CommandBuilder


class TestBulk:
    @pytest.mark.skip
    def test_it_requires_authentication(self, app):
        response = app.post("/api/bulk", b"dummy", headers=None, expect_errors=True)

        assert response.status_int == 404

    def test_it_accepts_a_valid_request(self, app, nd_json, auth_header):
        response = app.post("/api/bulk", nd_json, headers=auth_header)

        assert response.status_int == 200
        assert response.content_type == "application/x-ndjson"
        assert (
            response.headers["Hypothesis-Media-Type"]
            == "application/vnd.hypothesis.v1+x-ndjson"
        )

    def test_it_raises_errors_for_invalid_request(self, app, auth_header):
        response = app.post(
            "/api/bulk", '["some-mince"]', headers=auth_header, expect_errors=True
        )

        assert response.status_int == 400
        assert response.content_type == "application/json"

        assert response.json == {
            "errors": Any.list.comprised_of(
                Any.dict.containing({"code": "SchemaValidationError"})
            )
        }

    @pytest.fixture
    def commands(self):
        return [
            CommandBuilder.configure("acct:user1@example.com", total_instructions=4),
            CommandBuilder.user.upsert(
                "acct:user2@example.com",
                {
                    "username": "user2",
                    "display_name": "display_name",
                    "authority": "example.com",
                    "identities": [
                        {
                            "provider": "provider",
                            "provider_unique_id": "provider_unique_id",
                        }
                    ],
                },
            ),
            CommandBuilder.group.upsert(
                {"groupid": "group:name@example.com", "name": "name"}, "group_ref"
            ),
            CommandBuilder.group_membership.create(
                "acct:user2@example.com", "group_ref"
            ),
        ]

    @pytest.fixture
    def nd_json(self, commands):
        return "\n".join(json.dumps(command.raw) for command in commands)


@pytest.fixture
def auth_header():
    # When authentication is on, this should be enabled
    return
