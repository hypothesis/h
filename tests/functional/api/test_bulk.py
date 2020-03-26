import json

import pytest
from h_matchers import Any

from h.h_api.bulk_api import CommandBuilder


class TestBulk:
    def test_it_requires_authentication(self, app, bad_header):
        response = app.post(
            "/api/bulk", b"dummy", headers=bad_header, expect_errors=True
        )

        assert response.status_int == 404

    def test_it_accepts_a_valid_request(self, app, nd_json, lms_auth_header):
        response = app.post("/api/bulk", nd_json, headers=lms_auth_header)

        assert response.status_int == 200
        assert response.content_type == "application/x-ndjson"
        assert (
            response.headers["Hypothesis-Media-Type"]
            == "application/vnd.hypothesis.v1+x-ndjson"
        )

    def test_it_raises_errors_for_invalid_request(self, app, lms_auth_header):
        response = app.post(
            "/api/bulk", '["some-mince"]', headers=lms_auth_header, expect_errors=True
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
        authority = "lms.hypothes.is"

        return [
            CommandBuilder.configure(f"acct:user1@{authority}", total_instructions=4),
            CommandBuilder.user.upsert(
                {
                    "username": "user2",
                    "display_name": "display_name",
                    "authority": authority,
                    "identities": [
                        {
                            "provider": "provider",
                            "provider_unique_id": "provider_unique_id",
                        }
                    ],
                },
                "user_ref",
            ),
            CommandBuilder.group.upsert(
                {
                    "authority": authority,
                    "authority_provided_id": "name",
                    "name": "name",
                },
                "group_ref",
            ),
            CommandBuilder.group_membership.create("user_ref", "group_ref"),
        ]

    @pytest.fixture
    def nd_json(self, commands):
        return "\n".join(json.dumps(command.raw) for command in commands)

    @pytest.fixture(params=[None, "token", "non_lms_auth"])
    def bad_header(self, request, token_auth_header, auth_header):
        yield {"token": token_auth_header, "non_lms_auth": auth_header}.get(
            request.param, request.param
        )

    @pytest.fixture
    def lms_auth_header(self, auth_header_for_authority):
        return auth_header_for_authority("lms.hypothes.is")
