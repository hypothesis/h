import json

import pytest
from h_matchers import Any

from h.h_api.bulk_api import CommandBuilder
from h.h_api.enums import ViewType
from h.models import User


class TestBulk:
    AUTHORITY = "lms.hypothes.is"

    def test_it_requires_authentication(self, app, bad_header):
        response = app.post(
            "/api/bulk", b"dummy", headers=bad_header, expect_errors=True
        )

        assert response.status_int == 404

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

    def test_it_accepts_a_valid_request(
        self, app, nd_json, lms_auth_header, db_session
    ):
        app.post("/api/bulk", nd_json, headers=lms_auth_header)

        response = app.post("/api/bulk", nd_json, headers=lms_auth_header)

        assert response.status_int == 200
        assert response.content_type == "application/x-ndjson"
        assert (
            response.headers["Hypothesis-Media-Type"]
            == "application/vnd.hypothesis.v1+x-ndjson"
        )

        self._assert_response_has_expected_values(response)

    @staticmethod
    def _assert_response_has_expected_values(response):
        lines = response.body.decode("utf-8").split("\n")
        lines = [json.loads(line) for line in lines if line]

        assert lines == [
            {"data": {"id": Any(), "type": "user"}},
            {"data": {"id": Any(), "type": "group"}},
            {"data": {"id": Any(), "type": "group"}},
            {"data": {"id": Any(), "type": "group"}},
            {"data": {"id": Any(), "type": "group_membership"}},
            {"data": {"id": Any(), "type": "group_membership"}},
            {"data": {"id": Any(), "type": "group_membership"}},
        ]

    @pytest.fixture
    def commands(self, user):
        group_count = 3

        commands = [
            CommandBuilder.configure(
                user.userid, total_instructions=group_count * 2 + 2, view=ViewType.BASIC
            ),
            CommandBuilder.user.upsert(
                {
                    "username": "user2",
                    "display_name": "display_name",
                    "authority": self.AUTHORITY,
                    "identities": [
                        {
                            "provider": "provider",
                            "provider_unique_id": "provider_unique_id",
                        }
                    ],
                },
                "user_ref",
            ),
        ]

        for i in range(group_count):
            commands.append(
                CommandBuilder.group.upsert(
                    {
                        "authority": self.AUTHORITY,
                        "authority_provided_id": f"id_{i}",
                        "name": f"name_{i}",
                    },
                    f"group_ref_{i}",
                )
            )

        for i in range(group_count):
            commands.append(
                CommandBuilder.group_membership.create("user_ref", f"group_ref_{i}")
            )

        return commands

    @pytest.fixture
    def user(self, db_session):
        user = User(authority=self.AUTHORITY, _username="username")
        db_session.add(user)
        db_session.flush()

        return user

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
